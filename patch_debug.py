with open(r'contacts\views\bulk_send.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find where the API rejection is logged and add detail
old = "logger.warning(f'[Bulk Send] API rejection for {number} — not retrying.')"
new = """logger.warning(f'[Bulk Send] API rejection for {number} — not retrying. Status: {resp.status_code} Body: {resp.text[:300]}')"""

if old in content:
    content = content.replace(old, new)
    with open(r'contacts\views\bulk_send.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patched')
else:
    # Try to find the rejection log line whatever it looks like
    import re
    m = re.search(r'(logger\.\w+.*API rejection.*not retrying.*)', content)
    if m:
        print('Found line:', repr(m.group(1)))
    else:
        print('Not found - searching for resp variable name:')
        idx = content.find('not retrying')
        if idx >= 0:
            print(repr(content[idx-200:idx+100]))
