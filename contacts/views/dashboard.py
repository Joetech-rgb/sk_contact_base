import json
import threading
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import TruncDay
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from contacts.models import (
    CategoryChangeRequest,
    AccountLink, BulkMessage, Campaign, Category,
    CommunityPost, Contact, GoogleToken, ReferralSource, WhatsAppLog,
)
from contacts.views.permissions import admin_required


# ──────────────────────────────────────────────────────────────────
#  MAIN DASHBOARD
# ──────────────────────────────────────────────────────────────────

@login_required
@admin_required
def sk_dashboard_view(request):
    today = timezone.now().date()

    # ── Core counts ───────────────────────────────────────────────
    total_contacts = Contact.objects.count()
    today_contacts = Contact.objects.filter(date_added__date=today).count()

    # ── Referral stats ────────────────────────────────────────────
    referral_sources = ReferralSource.objects.all()
    total_clicks     = sum(r.click_count for r in referral_sources)

    referral_stats = []
    for ref in referral_sources:
        reg_count = Contact.objects.filter(referral_source=ref).count()
        referral_stats.append({
            "label":         ref.label,
            "clicks":        ref.click_count,
            "registrations": reg_count,
        })

    referral_conversion_stats = []
    for r in referral_stats:
        rate = round((r["registrations"] / r["clicks"]) * 100) if r["clicks"] else 0
        referral_conversion_stats.append({**r, "conversion_rate": rate})

    overall_conversion_rate = (
        round((total_contacts / total_clicks) * 100) if total_clicks else 0
    )

    # ── Daily registrations (last 14 days) ────────────────────────
    two_weeks_ago = today - timedelta(days=13)
    daily_registrations = (
        Contact.objects
        .filter(date_added__date__gte=two_weeks_ago)
        .annotate(day=TruncDay("date_added"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    # ── 30-day chart ──────────────────────────────────────────────
    thirty_days_ago = today - timedelta(days=29)
    chart_qs = (
        Contact.objects
        .filter(date_added__date__gte=thirty_days_ago)
        .annotate(day=TruncDay("date_added"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    chart_map    = {entry["day"].date(): entry["count"] for entry in chart_qs}
    chart_labels = []
    chart_values = []
    for i in range(30):
        d = thirty_days_ago + timedelta(days=i)
        chart_labels.append(d.strftime("%d %b"))
        chart_values.append(chart_map.get(d, 0))

    # ── Platform stats ────────────────────────────────────────────
    platform_stats = (
        Contact.objects
        .exclude(platform="")
        .values("platform")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # ── Country list ──────────────────────────────────────────────
    country_list = (
        Contact.objects
        .exclude(country="")
        .values_list("country", flat=True)
        .distinct()
        .order_by("country")
    )

    # ── Categories ────────────────────────────────────────────────
    categories = Category.objects.order_by("name")

    # ── Bulk send history ─────────────────────────────────────────
    bulk_history = BulkMessage.objects.select_related("created_by").order_by("-created_at")[:20]

    # ── Campaigns ─────────────────────────────────────────────────
    campaigns = Campaign.objects.prefetch_related("target_categories").order_by("-created_at")

    # ── Community posts ───────────────────────────────────────────
    community_posts = CommunityPost.objects.all()
    category_change_requests = CategoryChangeRequest.objects.select_related("requested_category").order_by("-submitted_at")[:50]

    # ── Account links ─────────────────────────────────────────────
    account_links_qs  = AccountLink.objects.all()
    account_links     = {a.platform: a for a in account_links_qs}
    total_shares      = sum(a.shares for a in account_links_qs)

    # FIX: serialise account links to JSON for the dashboard JS block
    account_links_json = json.dumps({
        a.platform: {
            "handle":    a.handle,
            "url":       a.url,
            "followers": a.followers,
            "shares":    a.shares,
        }
        for a in account_links_qs
    })

    # ── WhatsApp log (inbox feed) ─────────────────────────────────
    wa_logs = WhatsAppLog.objects.select_related("contact").order_by("-timestamp")[:50]

    # ── WhatsApp delivery summary ─────────────────────────────────
    wa_sent   = WhatsAppLog.objects.filter(status="sent").count()
    wa_failed = WhatsAppLog.objects.filter(status="failed").count()
    wa_total  = wa_sent + wa_failed
    wa_rate   = round((wa_sent / wa_total) * 100) if wa_total else 0

    # ── Google OAuth ──────────────────────────────────────────────
    from contacts.models import WhatsAppTemplate
    wa_templates = WhatsAppTemplate.objects.filter(is_active=True)

    google_token         = GoogleToken.objects.first()
    google_connected     = bool(google_token)
    google_account_email = google_token.email if google_token else ""

    # ── Paginate contacts ─────────────────────────────────────────
    contact_qs = Contact.objects.select_related("category", "referral_source")
    search     = request.GET.get("q", "").strip()
    f_cat      = request.GET.get("f_cat", "").strip()
    f_country  = request.GET.get("f_country", "").strip()
    f_platform = request.GET.get("f_platform", "").strip()

    if search:
        contact_qs = contact_qs.filter(
            Q(first_name__icontains=search) |
            Q(surname__icontains=search) |
            Q(whatsapp_number__icontains=search) |
            Q(handle__icontains=search)
        )
    if f_cat:      contact_qs = contact_qs.filter(category__name__iexact=f_cat)
    if f_country:  contact_qs = contact_qs.filter(country__iexact=f_country)
    if f_platform: contact_qs = contact_qs.filter(platform__iexact=f_platform)

    paginator = Paginator(contact_qs, 50)
    page      = request.GET.get("page", 1)
    contacts  = paginator.get_page(page)

    return render(request, "contacts/sk_dashboard.html", {
        # Analytics
        "total_contacts":            total_contacts,
        "today_contacts":            today_contacts,
        "total_clicks":              total_clicks,
        "overall_conversion_rate":   overall_conversion_rate,
        "referral_stats":            referral_stats,
        "referral_conversion_stats": referral_conversion_stats,
        "daily_registrations":       daily_registrations,
        "chart_labels_json":         json.dumps(chart_labels),
        "chart_values_json":         json.dumps(chart_values),
        # Contacts
        "platform_stats":            platform_stats,
        "country_list":              country_list,
        "categories":                categories,
        "contacts":                  contacts,
        "search":                    search,
        "f_cat":                     f_cat,
        "f_country":                 f_country,
        "f_platform":                f_platform,
        # Bulk
        "bulk_history":              bulk_history,
        # Campaigns
        "campaigns":                 campaigns,
        # Posts
        "community_posts":           community_posts,
        # Account links
        "account_links":             account_links,
        "account_links_json":        account_links_json,   # FIX: was missing
        "total_shares":              total_shares,
        # WhatsApp inbox
        "wa_logs":                   wa_logs,
        "wa_sent":                   wa_sent,
        "wa_failed":                 wa_failed,
        "wa_rate":                   wa_rate,
        # Google
        "wa_templates":              wa_templates,
        "google_connected":          google_connected,
        "google_account_email":      google_account_email,
        "category_change_requests":  category_change_requests,
    })


# ──────────────────────────────────────────────────────────────────
#  CAMPAIGN CRUD APIS
# ──────────────────────────────────────────────────────────────────

@login_required
@admin_required
@require_POST
def campaign_create_view(request):
    name             = request.POST.get("name", "").strip()
    country          = request.POST.get("country", "").strip()
    template         = request.POST.get("template", "").strip()
    notes            = request.POST.get("notes", "").strip()
    campaign_message = request.POST.get("campaign_message", "").strip()
    cat_ids          = request.POST.getlist("categories")

    if not name:
        from django.contrib import messages
        messages.error(request, "Campaign name is required.")
        return redirect("dashboard")

    camp = Campaign.objects.create(
        name=name,
        target_country=country,
        template_name=template,
        campaign_message=campaign_message,
        notes=notes,
        status="draft",
    )
    if cat_ids:
        camp.target_categories.set(Category.objects.filter(pk__in=cat_ids))

    return redirect("dashboard")


@login_required
@admin_required
@require_POST
def campaign_update_view(request, pk):
    camp = get_object_or_404(Campaign, pk=pk)
    field = request.POST.get("field")
    value = request.POST.get("value")
    if field in ("contacted_count", "responded_count", "confirmed_count"):
        try:
            setattr(camp, field, int(value))
            camp.save(update_fields=[field])
        except (ValueError, TypeError):
            pass
    elif field == "status" and value in ("draft", "active", "complete"):
        camp.status = value
        camp.save(update_fields=["status"])
    return JsonResponse({"ok": True, "response_rate": camp.response_rate, "conversion_rate": camp.conversion_rate})


@login_required
@admin_required
@require_POST
def campaign_increment_contacted(request, pk):
    camp = get_object_or_404(Campaign, pk=pk)
    camp.contacted_count += 1
    camp.save()
    return JsonResponse({"ok": True, "contacted_count": camp.contacted_count})


# FIX: added @login_required and @admin_required — was completely unprotected
@login_required
@admin_required
@require_POST
def campaign_contact_status_api(request, camp_pk, contact_pk):
    from contacts.models import CampaignContact
    camp    = get_object_or_404(Campaign, pk=camp_pk)
    contact = get_object_or_404(Contact,  pk=contact_pk)
    status  = request.POST.get("status", "pending")
    cc, _   = CampaignContact.objects.get_or_create(campaign=camp, contact=contact)
    cc.status = status
    cc.save()
    camp.responded_count = CampaignContact.objects.filter(campaign=camp, status__in=["interested", "confirmed"]).count()
    camp.confirmed_count = CampaignContact.objects.filter(campaign=camp, status="confirmed").count()
    camp.save()
    return JsonResponse({
        "ok":              True,
        "status":          status,
        "responded_count": camp.responded_count,
        "confirmed_count": camp.confirmed_count,
    })


# FIX: added @login_required and @admin_required — was completely unprotected
@login_required
@admin_required
def campaign_contacts_api(request, pk):
    camp = get_object_or_404(Campaign, pk=pk)
    qs   = Contact.objects.all()
    cats = camp.target_categories.all()
    if cats.exists():
        qs = qs.filter(category__in=cats)
    if camp.target_country:
        qs = qs.filter(country=camp.target_country)

    message  = camp.campaign_message or ""
    contacts = []
    for c in qs:
        first_name   = c.full_name.split()[0] if c.full_name else "there"
        personalised = message.replace("{name}", first_name)
        clean_number = c.whatsapp_number.replace("+", "").replace(" ", "").strip()
        import urllib.parse
        wa_link = "https://wa.me/" + clean_number + "?text=" + urllib.parse.quote(personalised)
        contacts.append({
            "pk":       c.pk,
            "name":     c.full_name,
            "number":   c.full_whatsapp,
            "category": c.category.name if c.category else "-",
            "wa_link":  wa_link,
            "message":  personalised,
        })
    return JsonResponse({"ok": True, "contacts": contacts, "total": len(contacts), "campaign": camp.name})


# FIX: added @login_required, @admin_required, and @require_POST
# Previously accepted GET which meant any link visit would delete the campaign
@login_required
@admin_required
@require_POST
def campaign_delete_view(request, pk):
    Campaign.objects.filter(pk=pk).delete()
    return JsonResponse({"ok": True})


# ──────────────────────────────────────────────────────────────────
#  COMMUNITY POST APIS
# ──────────────────────────────────────────────────────────────────

@login_required
@admin_required
@require_POST
def post_create_view(request):
    post = CommunityPost.objects.create(
        type       = request.POST.get("type", "announcement"),
        title      = request.POST.get("title", "").strip(),
        content    = request.POST.get("content", "").strip(),
        author     = request.POST.get("author", "").strip(),
        is_visible = True,
    )
    return JsonResponse({
        "ok":      True,
        "pk":      post.pk,
        "type":    post.type,
        "title":   post.title,
        "content": post.content[:120],
        "date":    post.created_at.strftime("%d %b %Y"),
    })


@login_required
@admin_required
@require_POST
def post_toggle_view(request, pk):
    post = get_object_or_404(CommunityPost, pk=pk)
    post.is_visible = not post.is_visible
    post.save(update_fields=["is_visible"])
    return JsonResponse({"ok": True, "is_visible": post.is_visible})


@login_required
@admin_required
@require_POST
def post_delete_view(request, pk):
    CommunityPost.objects.filter(pk=pk).delete()
    return JsonResponse({"ok": True})


# ──────────────────────────────────────────────────────────────────
#  ACCOUNT LINK SAVE API
# ──────────────────────────────────────────────────────────────────

@login_required
@admin_required
@require_POST
def account_link_save_view(request):
    platform  = request.POST.get("platform", "").strip()
    handle    = request.POST.get("handle", "").strip()
    url       = request.POST.get("url", "").strip()
    followers = request.POST.get("followers", "").strip()
    shares    = int(request.POST.get("shares", 0) or 0)

    if not platform:
        return JsonResponse({"error": "Platform required"}, status=400)

    obj, _ = AccountLink.objects.update_or_create(
        platform=platform,
        defaults={"handle": handle, "url": url, "followers": followers, "shares": shares},
    )
    return JsonResponse({
        "ok":        True,
        "handle":    obj.handle,
        "url":       obj.url,
        "followers": obj.followers,
        "shares":    obj.shares,
    })


# ──────────────────────────────────────────────────────────────────
#  WHATSAPP TEMPLATE SAVE API
# ──────────────────────────────────────────────────────────────────

@login_required
@admin_required
@require_POST
def template_save_view(request):
    from contacts.models import WhatsAppTemplate
    name  = request.POST.get("name", "").strip()
    label = request.POST.get("label", "").strip()
    if not name:
        return JsonResponse({"error": "Name required"}, status=400)
    obj, _ = WhatsAppTemplate.objects.update_or_create(
        name=name, defaults={"label": label, "is_active": True}
    )
    return JsonResponse({"ok": True, "name": obj.name, "label": obj.label})


# ──────────────────────────────────────────────────────────────────
#  CATEGORY CHANGE REQUEST APPLY / REJECT
# ──────────────────────────────────────────────────────────────────

@login_required
@admin_required
@require_POST
def catrequest_apply_view(request, pk):
    from contacts.models import CategoryChangeRequest, Contact
    from django.utils import timezone as _tz
    req = get_object_or_404(CategoryChangeRequest, pk=pk)
    if req.status != "pending":
        return JsonResponse({"ok": False, "error": "Request is not pending."})
    try:
        contact = Contact.objects.get(whatsapp_number=req.whatsapp_number)
        contact.category = req.requested_category
        contact.save(update_fields=["category"])
    except Contact.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Contact not found with that WhatsApp number."})
    req.status      = "done"
    req.resolved_at = _tz.now()
    req.save(update_fields=["status", "resolved_at"])
    return JsonResponse({"ok": True})


@login_required
@admin_required
@require_POST
def catrequest_reject_view(request, pk):
    from contacts.models import CategoryChangeRequest
    from django.utils import timezone as _tz
    req = get_object_or_404(CategoryChangeRequest, pk=pk)
    req.status      = "rejected"
    req.resolved_at = _tz.now()
    req.save(update_fields=["status", "resolved_at"])
    return JsonResponse({"ok": True})