# contacts/views/dashboard.py
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone
from ..models import Category, Contact, ReferralSource


@login_required(login_url="login")
def sk_dashboard_view(request):
    now   = timezone.now()
    today = now.date()
    total_contacts      = Contact.objects.count()
    today_contacts      = Contact.objects.filter(date_added__date=today).count()
    this_week_contacts  = Contact.objects.filter(date_added__gte=now - timedelta(days=7)).count()
    this_month_contacts = Contact.objects.filter(date_added__gte=now - timedelta(days=30)).count()
    first_contact = Contact.objects.order_by("date_added").first()
    days_since_start = (today - first_contact.date_added.date()).days if first_contact else 0
    category_stats  = Contact.objects.values("category__name").annotate(count=Count("id")).order_by("-count")
    country_stats   = Contact.objects.values("country").annotate(count=Count("id")).order_by("-count")[:10]
    platform_stats  = Contact.objects.exclude(platform="").values("platform").annotate(count=Count("id")).order_by("-count")
    recent_contacts = Contact.objects.select_related("category").order_by("-date_added")[:10]
    all_categories  = Category.objects.annotate(contact_count=Count("contact")).order_by("name")
    referral_sources = ReferralSource.objects.order_by("-click_count")
    return render(request, "contacts/sk_dashboard.html", {
        "total_contacts":      total_contacts,
        "today_contacts":      today_contacts,
        "this_week_contacts":  this_week_contacts,
        "this_month_contacts": this_month_contacts,
        "days_since_start":    days_since_start,
        "category_stats":      category_stats,
        "country_stats":       country_stats,
        "platform_stats":      platform_stats,
        "recent_contacts":     recent_contacts,
        "all_categories":      all_categories,
        "referral_sources":    referral_sources,
    })
