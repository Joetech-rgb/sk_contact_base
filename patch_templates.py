with open(r'contacts\views\dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '    google_token        = GoogleToken.objects.first()'
new = '''    from contacts.models import WhatsAppTemplate
    wa_templates = WhatsAppTemplate.objects.filter(is_active=True)

    google_token        = GoogleToken.objects.first()'''

if old in content:
    content = content.replace(old, new)
    with open(r'contacts\views\dashboard.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Step 1 OK')
else:
    print('Pattern not found')
