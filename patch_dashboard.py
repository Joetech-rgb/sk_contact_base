content = open('contacts/views/dashboard.py', encoding='utf-8').read()

old = '    referral_sources = ReferralSource.objects.order_by("-click_count")'
new = (
    '    referral_sources = ReferralSource.objects.order_by("-click_count")\n'
    '\n'
    '    # Chart data: registrations per day for last 30 days\n'
    '    from django.db.models.functions import TruncDate\n'
    '    import json\n'
    '    daily_qs = (\n'
    '        Contact.objects\n'
    '        .filter(date_added__gte=now - timedelta(days=29))\n'
    '        .annotate(day=TruncDate("date_added"))\n'
    '        .values("day")\n'
    '        .annotate(count=Count("id"))\n'
    '        .order_by("day")\n'
    '    )\n'
    '    # Fill in zeros for missing days\n'
    '    from datetime import date as date_type\n'
    '    day_map = {r["day"]: r["count"] for r in daily_qs}\n'
    '    chart_labels = []\n'
    '    chart_values = []\n'
    '    for i in range(29, -1, -1):\n'
    '        d = (now - timedelta(days=i)).date()\n'
    '        chart_labels.append(d.strftime("%b %d"))\n'
    '        chart_values.append(day_map.get(d, 0))\n'
    '    chart_labels_json = json.dumps(chart_labels)\n'
    '    chart_values_json = json.dumps(chart_values)\n'
    '\n'
    '    # Referral conversion: clicks vs registrations\n'
    '    referral_sources = ReferralSource.objects.order_by("-click_count")'
)
content = content.replace(old, new, 1)

# Add chart data to context
old2 = '        "active_notifications":  active_notifications,'
new2 = (
    '        "chart_labels_json":     chart_labels_json,\n'
    '        "chart_values_json":     chart_values_json,\n'
    '        "active_notifications":  active_notifications,'
)
content = content.replace(old2, new2, 1)

open('contacts/views/dashboard.py', 'w', encoding='utf-8').write(content)
print('dashboard.py patched OK')
