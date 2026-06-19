with open(r'contacts\views\bulk.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    if not isinstance(extra_params, list):\n        extra_params = []',
    '    if not isinstance(extra_params, list):\n        extra_params = []\n    language = data.get("language", "en")'
)
content = content.replace(
    '        args=(bulk.pk, contact_ids, template, extra_params),\n        daemon=True,\n    ).start()\n\n    return JsonResponse({\n        "success"',
    '        args=(bulk.pk, contact_ids, template, extra_params, language),\n        daemon=True,\n    ).start()\n\n    return JsonResponse({\n        "success"'
)

with open(r'contacts\views\bulk.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
