# contacts/views/bulk.py
import time
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from ..models import BulkMessage, Contact, ServiceRequest


@login_required(login_url="login")
def bulk_compose_view(request):
    qs = Contact.objects.all()
    category = request.GET.get("category", "").strip()
    country  = request.GET.get("country",  "").strip()
    platform = request.GET.get("platform", "").strip()
    if category: qs = qs.filter(category__name__iexact=category)
    if country:  qs = qs.filter(country__iexact=country)
    if platform: qs = qs.filter(platform__iexact=platform)
    preview_count = qs.count()

    if request.method == "POST":
        template = request.POST.get("template", "").strip()
        category = request.POST.get("category", "").strip()
        country  = request.POST.get("country",  "").strip()
        platform = request.POST.get("platform", "").strip()
        if not template:
            messages.error(request, "Template name is required.")
            return redirect("bulk-compose")
        qs = Contact.objects.all()
        if category: qs = qs.filter(category__name__iexact=category)
        if country:  qs = qs.filter(country__iexact=country)
        if platform: qs = qs.filter(platform__iexact=platform)
        bulk = BulkMessage.objects.create(
            template=template,
            filter_params={"category": category, "country": country, "platform": platform},
            status="sending",
            created_by=request.user,
        )
        from ..services.whatsapp import send_whatsapp
        sent = failed = 0
        for contact in qs.iterator():
            success = send_whatsapp(
                to=contact.full_whatsapp,
                template=template,
                params=[contact.first_name, str(contact.pk)],
                contact=contact,
            )
            if success: sent += 1
            else: failed += 1
            time.sleep(0.75)
        bulk.sent_count   = sent
        bulk.failed_count = failed
        bulk.status       = "done"
        bulk.save()
        messages.success(request, f"Bulk send complete. Sent: {sent}  Failed: {failed}")
        return redirect("bulk-history")

    return render(request, "contacts/bulk_compose.html", {
        "preview_count": preview_count,
        "filters": {"category": category, "country": country, "platform": platform},
    })


@login_required(login_url="login")
def bulk_history_view(request):
    history = BulkMessage.objects.select_related("created_by").order_by("-created_at")
    return render(request, "contacts/bulk_history.html", {"history": history})


@login_required(login_url="login")
def bulk_preview_api(request):
    qs = Contact.objects.all()
    category = request.GET.get("category", "").strip()
    country  = request.GET.get("country",  "").strip()
    platform = request.GET.get("platform", "").strip()
    if category: qs = qs.filter(category__name__iexact=category)
    if country:  qs = qs.filter(country__iexact=country)
    if platform: qs = qs.filter(platform__iexact=platform)
    return JsonResponse({"count": qs.count()})


def service_request_view(request):
    if request.method == "POST":
        name    = request.POST.get("name",    "").strip()
        email   = request.POST.get("email",   "").strip()
        phone   = request.POST.get("phone",   "").strip()
        budget  = request.POST.get("budget",  "").strip()
        notes   = request.POST.get("notes",   "").strip()
        category       = request.POST.get("category", "").strip()
        country        = request.POST.get("country",  "").strip()
        platform       = request.POST.get("platform", "").strip()
        follower_range = request.POST.get("follower_range", "").strip()
        if not name or not email or not phone:
            messages.error(request, "Name, email, and phone are required.")
            return redirect("service-request")
        sr = ServiceRequest.objects.create(
            requester_name  = name,
            email           = email,
            phone           = phone,
            budget          = budget,
            notes           = notes,
            filter_criteria = {
                "category":       category,
                "country":        country,
                "platform":       platform,
                "follower_range": follower_range,
            },
        )
        try:
            from django.conf import settings
            from ..services.whatsapp import send_whatsapp
            admin_phone = getattr(settings, "SK_ADMIN_WHATSAPP", "")
            if admin_phone:
                send_whatsapp(
                    to=admin_phone,
                    template="new_service_request",
                    params=[name, email, f"#{sr.pk}"],
                )
        except Exception:
            pass
        messages.success(request, "Your request has been submitted. We will be in touch shortly.")
        return redirect("service-request-thanks")
    return render(request, "contacts/service_request.html")


def service_request_thanks_view(request):
    return render(request, "contacts/service_request_thanks.html")
