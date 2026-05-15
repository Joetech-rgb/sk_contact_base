# contacts/views/public.py
from django.shortcuts import redirect, render
from ..models import Contact, ReferralSource
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
            contact.save()
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

    return render(request, "contacts/landing.html", {
        "form":           form,
        "total_contacts": Contact.objects.count(),
        "ref_slug":       ref_slug,
    })


def thank_you_view(request):
    return render(request, "contacts/thank_you.html", {
        "contact_number": request.session.get("contact_number", ""),
        "contact_name":   request.session.get("contact_name", ""),
        "total_contacts": Contact.objects.count(),
    })
