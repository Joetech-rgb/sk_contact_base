with open(r'contacts\services\whatsapp.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = 'def send_whatsapp(to: str, template: str, params: list, contact=None, footer: str = "") -> bool:'
new = 'def send_whatsapp(to: str, template: str, params: list, contact=None, footer: str = "", language: str = "en") -> bool:'

if old in content:
    content = content.replace(old, new)
    print('Step 1 OK')
else:
    print('Step 1 FAILED')

old2 = '"language": {"code": "en"}'
new2 = '"language": {"code": language}'

if old2 in content:
    content = content.replace(old2, new2)
    print('Step 2 OK')
else:
    print('Step 2 FAILED')

with open(r'contacts\services\whatsapp.py', 'w', encoding='utf-8') as f:
    f.write(content)
