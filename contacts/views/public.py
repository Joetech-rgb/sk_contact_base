# contacts/views/public.py
from django.shortcuts import redirect, render
from ..models import Contact, Notification, ReferralSource
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
            template="welcome_registration",
            params=[contact.first_name, str(contact.pk)],
            contact=contact,
        )
    except Exception:
        pass
