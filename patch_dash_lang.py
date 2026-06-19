with open(r'templates\contacts\sk_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

old = 'body:JSON.stringify({template:template, category:category, country:country, platform:platform, params:[]})'
new = '''body:JSON.stringify({template:template, category:category, country:country, platform:platform, params:[], language: template==='sk_welcome' ? 'en_US' : 'en'})'''

if old in content:
    content = content.replace(old, new)
    with open(r'templates\contacts\sk_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patched')
else:
    print('Not found')
