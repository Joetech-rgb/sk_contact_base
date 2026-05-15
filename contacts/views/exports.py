# contacts/views/exports.py
import csv as csv_mod
from datetime import date
from datetime import datetime as dt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from ..models import Contact


def _apply_filters(qs, request):
    cat      = request.GET.get("category",  "").strip()
    country  = request.GET.get("country",   "").strip()
    platform = request.GET.get("platform",  "").strip()
    dfrom    = request.GET.get("date_from", "").strip()
    dto      = request.GET.get("date_to",   "").strip()
    if cat:      qs = qs.filter(category__name__iexact=cat)
    if country:  qs = qs.filter(country__iexact=country)
    if platform: qs = qs.filter(platform__iexact=platform)
    if dfrom:
        try:    qs = qs.filter(date_added__date__gte=dt.strptime(dfrom, "%Y-%m-%d").date())
        except ValueError: pass
    if dto:
        try:    qs = qs.filter(date_added__date__lte=dt.strptime(dto, "%Y-%m-%d").date())
        except ValueError: pass
    return qs


@login_required(login_url="login")
def export_csv_view(request):
    qs = Contact.objects.select_related("category", "referral_source").order_by("-date_added")
    qs = _apply_filters(qs, request)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="sk_contacts_{date.today():%Y%m%d}.csv"'
    writer = csv_mod.writer(response)
    writer.writerow([
        "ID", "First Name", "Surname", "Email",
        "WhatsApp (full)", "Dial Code", "Country", "Region",
        "Age Range", "Platform", "Handle", "Follower Range",
        "Category", "School Category", "School Name", "Level/Year",
        "Referral Source", "Referral Slug", "Date Registered",
    ])
    for c in qs:
        writer.writerow([
            c.pk, c.first_name, c.surname, c.email,
            c.full_whatsapp, c.country_code, c.country, c.region, c.age_range,
            c.platform, c.handle_clean,
            c.get_follower_range_display() if c.follower_range else "",
            str(c.category) if c.category else "",
            c.get_school_category_display() if c.school_category else "",
            c.school_name,
            c.level_year if c.level_year is not None else "",
            str(c.referral_source) if c.referral_source else "",
            c.referral_slug,
            c.date_added.strftime("%Y-%m-%d %H:%M"),
        ])
    return response


@login_required(login_url="login")
def export_vcf_view(request):
    qs = Contact.objects.select_related("category", "referral_source").order_by("-date_added")
    qs = _apply_filters(qs, request)
    lines = []
    for c in qs:
        parts = [f"Platform: {c.platform}"]
        if c.handle_clean:   parts.append(f"Handle: @{c.handle_clean}")
        if c.follower_range: parts.append(f"Followers: {c.get_follower_range_display()}")
        if c.category:       parts.append(f"Category: {c.category}")
        parts.append(f"Country: {c.country}")
        parts.append(f"SK ID: #{c.pk}")
        lines += [
            "BEGIN:VCARD", "VERSION:3.0",
            f"N:{c.surname};{c.first_name};;;",
            f"FN:{c.first_name} {c.surname}",
            f"TEL;TYPE=CELL:{c.full_whatsapp}",
            f"EMAIL:{c.email}",
            f"NOTE:{' | '.join(parts)}",
            "END:VCARD", "",
        ]
    response = HttpResponse("\n".join(lines), content_type="text/vcard; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="sk_contacts_{date.today():%Y%m%d}.vcf"'
    return response
