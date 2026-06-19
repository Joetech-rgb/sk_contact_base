content = open('contacts/views/dashboard.py', encoding='utf-8').read()

# Add missing context variables
old = '    return render(request, "contacts/sk_dashboard.html", {'
new = (
    '    # Referral conversion stats\n'
    '    from django.db.models import Sum\n'
    '    referral_conversion_stats = []\n'
    '    total_clicks = 0\n'
    '    for ref in referral_sources:\n'
    '        clicks = ref.click_count or 0\n'
    '        regs = Contact.objects.filter(referral_source=ref).count()\n'
    '        rate = round((regs / clicks * 100), 1) if clicks > 0 else 0\n'
    '        referral_conversion_stats.append({\n'
    '            "label": ref.label if hasattr(ref, "label") else ref.slug,\n'
    '            "clicks": clicks,\n'
    '            "registrations": regs,\n'
    '            "conversion_rate": rate,\n'
    '        })\n'
    '        total_clicks += clicks\n'
    '    overall_conversion_rate = round((total_contacts / total_clicks * 100), 1) if total_clicks > 0 else 0\n'
    '\n'
    '    # Daily registrations table (last 14 days)\n'
    '    from django.db.models.functions import TruncDate as TruncDate2\n'
    '    daily_registrations = (\n'
    '        Contact.objects\n'
    '        .filter(date_added__gte=now - timedelta(days=13))\n'
    '        .annotate(day=TruncDate2("date_added"))\n'
    '        .values("day")\n'
    '        .annotate(count=Count("id"))\n'
    '        .order_by("-day")\n'
    '    )\n'
    '\n'
    '    # Country list for download filter\n'
    '    country_list = (\n'
    '        Contact.objects.exclude(country="")\n'
    '        .values_list("country", flat=True)\n'
    '        .distinct().order_by("country")\n'
    '    )\n'
    '\n'
    '    # Platform conversion stats\n'
    '    platform_conversion_stats = list(platform_stats)\n'
    '\n'
    '    # Referral stats for bar chart\n'
    '    referral_stats = referral_conversion_stats\n'
    '\n'
    '    return render(request, "contacts/sk_dashboard.html", {'
)
content = content.replace(old, new, 1)

# Add new vars to context
old2 = '        "active_notifications":  active_notifications,'
new2 = (
    '        "chart_labels_json":          chart_labels_json,\n'
    '        "chart_values_json":          chart_values_json,\n'
    '        "referral_conversion_stats":  referral_conversion_stats,\n'
    '        "referral_stats":             referral_stats,\n'
    '        "platform_conversion_stats":  platform_conversion_stats,\n'
    '        "daily_registrations":        daily_registrations,\n'
    '        "country_list":               country_list,\n'
    '        "total_clicks":               total_clicks,\n'
    '        "overall_conversion_rate":    overall_conversion_rate,\n'
    '        "active_notifications":  active_notifications,'
)
content = content.replace(old2, new2, 1)

open('contacts/views/dashboard.py', 'w', encoding='utf-8').write(content)
print('dashboard.py patched OK')
