with open('templates/contacts/sk_dashboard.html', 'rb') as f:
    raw = f.read()

# Try all possible encodings to find the right decode
for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
    try:
        text = raw.decode(enc)
        # Check if it decodes cleanly
        bad = text.count('\ufffd') + text.count('Ã')
        print(f'{enc}: {bad} bad chars, first 50: {repr(text[500:550])}')
    except Exception as e:
        print(f'{enc}: ERROR {e}')
