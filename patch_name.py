with open(r'contacts\views\bulk.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = 'params = [contact.name]'
new = 'params = [contact.first_name]'

if old in content:
    content = content.replace(old, new)
    with open(r'contacts\views\bulk.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patched')
else:
    print('Not found')
