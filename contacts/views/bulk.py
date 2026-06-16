import json
import time
import threading
import requests as _requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .permissions import require_group
from django.http import JsonResponse
from django.shortcuts import redirect, render
from ..models import BulkMessage, Contact, ServiceRequest


# FIX: module-level lock prevents two admins triggering duplicate bulk sends simultaneously
_bulk_send_lock = threading.Lock()


def _send_with_retry(contact, template, extra_params, retries=3, delay=8, language=None):
    """
    Attempt send_whatsapp up to `retries` times.
    - ConnectionError / network failures  → retry after `delay` seconds
    - False return from send_whatsapp     → do NOT retry (API-level rejection)
    Returns True on success, False on final failure.
    """
    from ..services.whatsapp import send_whatsapp

    for attempt in range(1, retries + 1):
        try:
            params = extra_params
            if template == "sk_opportunity" and not params:
                params = [contact.first_name]

            lang = language or ("en_US" if template == "sk_welcome" else "en")

            result = send_whatsapp(
                to=contact.full_whatsapp,
                template=template,
                params=params,
                contact=contact,
                language=lang,
            )
            if result:
                return True
            print(f"[Bulk Send] API rejection for {contact.full_whatsapp} — not retrying.")
            return False
        except (_requests.exceptions.ConnectionError,
                _requests.exceptions.Timeout) as exc:
            print(
                f"[Bulk Send] Network error for {contact.full_whatsapp} "
                f"— attempt {attempt}/{retries}: {exc}"
            )
            if attempt < retries:
                time.sleep(delay)

    print(f"[Bulk Send] Gave up on {contact.full_whatsapp} after {retries} attempts.")
    return False


def _do_bulk_send(bulk_id, contact_ids, template, extra_params=None, language="en_US"):
    """
    Runs in a background thread — sends messages one by one with retry support.
    FIX: thread is no longer daemon=True so it survives a server worker recycle.
    """
    from ..models import BulkMessage, Contact

    extra_params = extra_params or []
    sent = failed = 0

    for contact in Contact.objects.filter(pk__in=contact_ids).iterator():
        success = _send_with_retry(contact, template, extra_params, language=language)
        if success:
            sent += 1
        else:
            failed += 1

        # PATCHED: save every msg for small sends, every 10 for large
        _total_so_far = sent + failed
        _save_interval = 1 if len(contact_ids) <= 50 else 10
        if _total_so_far % _save_interval == 0:
            BulkMessage.objects.filter(pk=bulk_id).update(
                sent_count=sent,
                failed_count=failed,
            )

        time.sleep(0.75)

    BulkMessage.objects.filter(pk=bulk_id).update(
        sent_count=sent,
        failed_count=failed,
        status="done",
    )
    print(f"[Bulk Send] Done — Sent: {sent} | Failed: {failed}")


@login_required(login_url="login")
@require_group("Sender", "Full Admin")
def bulk_compose_view(request):
    qs       = Contact.objects.all()
    category = request.GET.get("category", "").strip()
    country  = request.GET.get("country",  "").strip()
    platform = request.GET.get("platform", "").strip()
    if category: qs = qs.filter(category__name__iexact=category)
    if country:  qs = qs.filter(country__iexact=country)
    if platform: qs = qs.filter(platform__iexact=platform)
    preview_count = qs.count()

    if request.method == "POST":
        template     = request.POST.get("template", "").strip()
        category     = request.POST.get("category", "").strip()
        country      = request.POST.get("country",  "").strip()
        platform     = request.POST.get("platform", "").strip()
        raw_params   = request.POST.get("params", "").strip()
        extra_params = [p.strip() for p in raw_params.split(",")] if raw_params else []

        if not template:
            messages.error(request, "Template name is required.")
            return redirect("bulk-compose")

        qs = Contact.objects.all()
        if category: qs = qs.filter(category__name__iexact=category)
        if country:  qs = qs.filter(country__iexact=country)
        if platform: qs = qs.filter(platform__iexact=platform)

        contact_ids = list(qs.values_list("pk", flat=True))
        if not contact_ids:
            messages.error(request, "No contacts match the selected filters.")
            return redirect("bulk-compose")

        bulk = BulkMessage.objects.create(
            template=template,
            filter_params={"category": category, "country": country, "platform": platform},
            status="sending",
            created_by=request.user,
            sent_count=0,
            failed_count=0,
        )

        # FIX: daemon=False — thread survives worker recycles
        t = threading.Thread(
            target=_do_bulk_send,
            args=(bulk.pk, contact_ids, template, extra_params),
            daemon=False,
        )
        t.start()

        messages.success(request, f"Bulk send started for {len(contact_ids)} contacts. Check history for progress.")
        return redirect("bulk-history")

    return render(request, "contacts/bulk_compose.html", {
        "preview_count": preview_count,
        "filters": {"category": category, "country": country, "platform": platform},
    })


@login_required(login_url="login")
@require_group("Viewer", "Sender", "Full Admin")
def bulk_history_view(request):
    history = BulkMessage.objects.select_related("created_by").order_by("-created_at")
    return render(request, "contacts/bulk_history.html", {"history": history})


@login_required(login_url="login")
def bulk_preview_api(request):
    qs        = Contact.objects.all()
    category  = request.GET.get("category",  "").strip()
    country   = request.GET.get("country",   "").strip()
    platform  = request.GET.get("platform",  "").strip()
    age_range = request.GET.get("age_range", "").strip()  # PATCHED
    if category:  qs = qs.filter(category__name__iexact=category)
    if country:   qs = qs.filter(country__iexact=country)
    if platform:  qs = qs.filter(platform__iexact=platform)
    if age_range: qs = qs.filter(age_range__iexact=age_range)  # PATCHED
    return JsonResponse({"count": qs.count()})


@login_required(login_url="login")
@require_group("Sender", "Full Admin")
def bulk_send_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    # FIX: prevent simultaneous bulk sends from two admin sessions
    if not _bulk_send_lock.acquire(blocking=False):
        return JsonResponse({"error": "A bulk send is already in progress. Please wait for it to finish."}, status=429)

    try:
        data         = json.loads(request.body)
        template     = data.get("template", "sk_welcome")
        category     = data.get("category", "").strip()
        country      = data.get("country",  "").strip()
        platform     = data.get("platform", "").strip()
        extra_params = data.get("params", [])
        if not isinstance(extra_params, list):
            extra_params = []
        language = data.get("language", "en_US")  # PATCHED: was "en"

        qs = Contact.objects.all()
        if category: qs = qs.filter(category__name__iexact=category)
        if country:  qs = qs.filter(country__iexact=country)
        if platform: qs = qs.filter(platform__iexact=platform)

        if not qs.exists():
            return JsonResponse({"error": "No contacts match the selected filters."}, status=400)

        contact_ids = list(qs.values_list("pk", flat=True))

        bulk = BulkMessage.objects.create(
            template=template,
            filter_params={"category": category, "country": country, "platform": platform},
            status="sending",
            created_by=request.user,
            sent_count=0,
            failed_count=0,
        )

        def run_and_release():
            try:
                _do_bulk_send(bulk.pk, contact_ids, template, extra_params, language)
            finally:
                # Always release the lock when the job finishes or crashes
                _bulk_send_lock.release()

        # FIX: daemon=False — thread survives worker recycles
        t = threading.Thread(target=run_and_release, daemon=False)
        t.start()

        return JsonResponse({
            "success": True,
            "message": f"Bulk send started for {len(contact_ids)} contacts.",
            "bulk_id": bulk.pk,
        })

    except Exception as exc:
        _bulk_send_lock.release()
        return JsonResponse({"error": str(exc)}, status=500)


@login_required(login_url="login")
def bulk_status_api(request, bulk_id):
    """Poll endpoint so the admin can check send progress."""
    try:
        bulk = BulkMessage.objects.get(pk=bulk_id)
        return JsonResponse({
            "status": bulk.status,
            "sent":   bulk.sent_count,
            "failed": bulk.failed_count,
            "total":  bulk.sent_count + bulk.failed_count,
        })
    except BulkMessage.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)


def service_request_view(request):
    if request.method == "POST":
        name           = request.POST.get("name",    "").strip()
        email          = request.POST.get("email",   "").strip()
        phone          = request.POST.get("phone",   "").strip()
        budget         = request.POST.get("budget",  "").strip()
        notes          = request.POST.get("notes",   "").strip()
        category       = request.POST.get("category", "").strip()
        country        = request.POST.get("country",  "").strip()
        platform       = request.POST.get("platform", "").strip()
        follower_range = request.POST.get("follower_range", "").strip()
        if not name or not email or not phone:
            messages.error(request, "Name, email, and phone are required.")
            return redirect("service-request")
        sr = ServiceRequest.objects.create(
            requester_name = name,
            email          = email,
            phone          = phone,
            budget         = budget,
            notes          = notes,
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