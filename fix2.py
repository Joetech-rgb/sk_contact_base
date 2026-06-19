with open('templates/contacts/sk_dashboard.html', 'r', encoding='utf-8', errors='replace') as f:
    text = f.read()

# The corrupted sequence represents these characters:
# long blob = em dash (—)
import re
text = re.sub(r'[Ã][^\s<>"]{2,80}(?=\s|<|>|")', lambda m: {
    True: '—'
}.get(True, m.group()), text)

# Simpler approach - replace all corrupted blobs with correct chars
bad = [
    ('\u00c3\u0192\u00c3\u2020\u00e2\u20ac\u2122\u00c3\u0192\u00e2\u20ac\u00c2\u00a0\u00c3\u00a2\u00c2\u00a0', '\u2014'),
]

# Just do direct byte-level fix
with open('templates/contacts/sk_dashboard.html', 'rb') as f:
    raw = f.read()

# Replace the specific corrupted em-dash pattern
import re as _re
# The corruption pattern for em-dash (—) in double-utf8
patterns = [
    (b'\xc3\x83\xc2\x86\xe2\x80\x99\xc3\x83\xc2\xa2\xe2\x82\xac\xc2\x9e\xc2\xa2', b'\xe2\x80\x94'),
    (b'\xc3\x83\xe2\x80\x9c\xc3\x83\xe2\x80\x94', b'\xe2\x80\x94'),
]

# Decode as latin1 then re-encode fix
text = raw.decode('latin-1')
# These are utf8 bytes interpreted as latin1 - double encoded
# Fix by encoding to latin1 bytes then decoding as utf8
try:
    fixed = text.encode('latin-1').decode('utf-8')
except:
    fixed = text

# Now replace em-dash variants
fixed = fixed.replace('\u2014', ' - ')
fixed = fixed.replace('\u2013', '-')
fixed = fixed.replace('\u2019', "'")
fixed = fixed.replace('\u201c', '"')
fixed = fixed.replace('\u201d', '"')
fixed = fixed.replace('\u2026', '...')
fixed = fixed.replace('\u00b7', '·')
fixed = fixed.replace('\u2022', '-')
fixed = fixed.replace('\u00a0', ' ')
fixed = fixed.replace('\u2192', '->')

with open('templates/contacts/sk_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(fixed)

print('Done!')
