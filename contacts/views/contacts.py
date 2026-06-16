# contacts/views/contacts.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from ..api_auth import require_api_key
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from ..forms import ContactForm
from ..models import Category, Contact


@login_required(login_url="login")
def contact_list_view(request):
    qs = Contact.objects.select_related("category", "referral_source").order_by("-date_added")
    search = request.GET.get("search", "").strip()
    if search:
        qs = qs.filter(
            Q(first_name__icontains=search) |
            Q(surname__icontains=search) |
            Q(email__icontains=search) |
            Q(whatsapp_number__icontains=search) |
            Q(handle__icontains=search)
        )
    cat      = request.GET.get("category", "").strip()
    country  = request.GET.get("country",  "").strip()
    platform = request.GET.get("platform", "").strip()
    if cat:      qs = qs.filter(category__name__iexact=cat)
    if country:  qs = qs.filter(country__iexact=country)
    if platform: qs = qs.filter(platform__iexact=platform)
    sort = request.GET.get("sort", "-date_added")
    if sort in ["-date_added", "date_added", "first_name", "-first_name"]:
        qs = qs.order_by(sort)
    return render(request, "contacts/contact_list.html", {
        "contacts":        qs,
        "total_contacts":  Contact.objects.count(),
        "today_contacts":  Contact.objects.filter(date_added__date=timezone.now().date()).count(),
        "categories":      Category.objects.filter(is_active=True),
        "countries":       Contact.objects.values_list("country", flat=True).distinct().order_by("country"),
        "current_filters": {"search": search, "category": cat, "country": country, "platform": platform, "sort": sort},
    })


@login_required(login_url="login")
def contact_add_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            # Send welcome WhatsApp message
            try:
                from ..services.whatsapp import send_whatsapp
                send_whatsapp(
                    to=contact.full_whatsapp,
                    template='sk_welcome',
                    params=[],          # sk_welcome template has no parameters
                    contact=contact,
                )
            except Exception:
                pass
            messages.success(request, "Contact added and welcome message sent!")
            return redirect("contact-list")
    else:
        form = ContactForm()
    return render(request, "contacts/contact_form.html", {"form": form, "title": "Add Contact"})


@login_required(login_url="login")
def contact_edit_view(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == "POST":
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, "Contact updated successfully!")
            return redirect("contact-list")
    else:
        form = ContactForm(instance=contact)
    return render(request, "contacts/contact_form.html", {"form": form, "title": "Edit Contact"})


@login_required(login_url="login")
def contact_delete_view(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == "POST":
        name = contact.full_name
        contact.delete()
        messages.success(request, f'"{name}" has been deleted.')
        return redirect("sk-dashboard")
    return render(request, "contacts/contact_confirm_delete.html", {"contact": contact})


@login_required(login_url="login")
@require_api_key
def contact_detail_api(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    return JsonResponse({
        "id":              contact.id,
        "first_name":      contact.first_name,
        "surname":         contact.surname,
        "full_name":       contact.full_name,
        "email":           contact.email,
        "whatsapp_number": contact.full_whatsapp,
        "whatsapp_url":    contact.whatsapp_chat_url,
        "category":        str(contact.category) if contact.category else "",
        "country":         contact.country,
        "platform":        contact.platform,
        "handle":          contact.handle_clean,
        "follower_range":  contact.get_follower_range_display() if contact.follower_range else "",
        "referral_source": str(contact.referral_source) if contact.referral_source else "",
        "date_added":      contact.date_added.strftime("%Y-%m-%d %H:%M"),
        "days_since_added": contact.days_since_added,
    })


@login_required(login_url="login")
@require_POST
def category_add_view(request):
    name = request.POST.get("name", "").strip()
    if not name:
        messages.error(request, "Category name is required.")
        return redirect("sk-dashboard")
    Category.objects.get_or_create(name=name, defaults={"is_active": True})
    messages.success(request, f'Category "{name}" added.')
    return redirect("sk-dashboard")


@login_required(login_url="login")
@require_POST
def category_toggle_view(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    cat.is_active = not cat.is_active
    cat.save(update_fields=["is_active"])
    messages.success(request, f'"{cat.name}" {"enabled" if cat.is_active else "disabled"} on registration form.')
    return redirect("sk-dashboard")


@login_required(login_url="login")
@require_POST
def category_delete_view(request, pk):
    cat  = get_object_or_404(Category, pk=pk)
    name = cat.name
    cat.delete()
    messages.success(request, f'"{name}" removed. Contact data preserved.')
    return redirect("sk-dashboard")