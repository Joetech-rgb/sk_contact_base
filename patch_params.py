with open(r'contacts\views\bulk.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''            result = send_whatsapp(
                to=contact.full_whatsapp,
                template=template,
                params=extra_params,
                contact=contact,
                language=language,
            )'''

new = '''            params = extra_params
            if template == "sk_opportunity" and not params:
                params = [contact.name]

            result = send_whatsapp(
                to=contact.full_whatsapp,
                template=template,
                params=params,
                contact=contact,
                language=language,
            )'''

if old in content:
    content = content.replace(old, new)
    with open(r'contacts\views\bulk.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patched')
else:
    print('Not found')
