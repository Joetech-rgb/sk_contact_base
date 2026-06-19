with open(r'contacts\views\public.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''        send_whatsapp(
            to=contact.full_whatsapp,
            template="sk_welcome",
            params=[],
            contact=contact,
        )'''

new = '''        send_whatsapp(
            to=contact.full_whatsapp,
            template="sk_welcome",
            params=[],
            contact=contact,
            language="en_US",
        )'''

if old in content:
    content = content.replace(old, new)
    with open(r'contacts\views\public.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patched')
else:
    print('Not found')
