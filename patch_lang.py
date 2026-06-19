with open(r'contacts\services\whatsapp.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '"language": {"code": "en_US"}'
new = '"language": {"code": "en"}'

if old in content:
    content = content.replace(old, new)
    with open(r'contacts\services\whatsapp.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patched to en')
else:
    print('Not found - searching:')
    idx = content.find('language')
    print(repr(content[idx:idx+50]))
