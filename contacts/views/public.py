# contacts/views/public.py
from django.shortcuts import redirect, render
from django.http import JsonResponse
from ..models import Contact, Notification, ReferralSource, CommunityPost, Category, CategoryChangeRequest
from ..forms import ContactForm


def landing_view(request):
    ref_slug = request.GET.get("ref", "").strip()
    referral_obj = None
    if ref_slug:
        try:
            referral_obj = ReferralSource.objects.get(slug=ref_slug, is_active=True)
            ReferralSource.objects.filter(pk=referral_obj.pk).update(
                click_count=referral_obj.click_count + 1
            )
        except ReferralSource.DoesNotExist:
            pass

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            if referral_obj and not contact.referral_source:
                contact.referral_source = referral_obj
            if ref_slug and not contact.referral_slug:
                contact.referral_slug = ref_slug
            from django.utils import timezone
            if form.cleaned_data.get("agree_to_terms"):
                contact.agreed_to_terms = timezone.now()
            contact.save()
            _send_welcome(contact)
            request.session["contact_number"] = contact.id
            request.session["contact_name"]   = contact.full_name
            return redirect("thank-you")
    else:
        initial = {}
        if referral_obj:
            initial["referral_source"] = referral_obj.pk
        if ref_slug:
            initial["referral_slug"] = ref_slug
        form = ContactForm(initial=initial)

    notifications = Notification.objects.filter(is_active=True).order_by("-created_at")[:3]

    return render(request, "contacts/landing.html", {
        "form":           form,
        "total_contacts": Contact.objects.count(),
        "ref_slug":       ref_slug,
        "notifications":  notifications,
        "community_posts":    CommunityPost.objects.filter(is_visible=True).order_by("-created_at"),
        "active_categories":  Category.objects.filter(is_active=True).order_by("name"),
    })


def thank_you_view(request):
    return render(request, "contacts/thank_you.html", {
        "contact_number": request.session.get("contact_number", ""),
        "contact_name":   request.session.get("contact_name", ""),
        "total_contacts": Contact.objects.count(),
    })


def _send_welcome(contact):
    try:
        from ..services.whatsapp import send_whatsapp
        send_whatsapp(
            to=contact.full_whatsapp,
            template="sk_welcome",
            params=[],
            contact=contact,
            language="en_US",
        )
    except Exception:
        pass


def category_change_request_view(request):
    """
    AJAX endpoint — user submits a category change request from the landing page.
    Returns JSON so it works without a page reload.
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)

    whatsapp      = request.POST.get("whatsapp_number", "").strip()
    full_name     = request.POST.get("full_name", "").strip()
    requested_id  = request.POST.get("requested_category", "").strip()
    reason        = request.POST.get("reason", "").strip()

    if not whatsapp or not requested_id:
        return JsonResponse({"ok": False, "error": "WhatsApp number and category are required."})

    try:
        category = Category.objects.get(pk=requested_id, is_active=True)
    except Category.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Invalid category selected."})

    # Block duplicate pending requests for the same number + category
    already = CategoryChangeRequest.objects.filter(
        whatsapp_number=whatsapp,
        requested_category=category,
        status="pending",
    ).exists()
    if already:
        return JsonResponse({
            "ok": False,
            "error": "You already have a pending request for this category.",
        })

    # Pull current category from the contact record if it exists
    current = ""
    try:
        contact = Contact.objects.get(whatsapp_number=whatsapp)
        current = contact.category.name if contact.category else ""
    except Contact.DoesNotExist:
        pass

    CategoryChangeRequest.objects.create(
        whatsapp_number=whatsapp,
        full_name=full_name,
        current_category=current,
        requested_category=category,
        reason=reason,
    )

    return JsonResponse({
        "ok": True,
        "message": "Request submitted! The admin will update your category shortly.",
    })