with open(r'contacts\views\dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '        "google_connected":          google_connected,'
new = '        "wa_templates":              wa_templates,\n        "google_connected":          google_connected,'

if old in content:
    content = content.replace(old, new)
    with open(r'contacts\views\dashboard.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Step 2 OK')
else:
    print('Pattern not found')
