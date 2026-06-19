import re

clean = open("templates/contacts/sk_dashboard.html.bak", "rb").read()

# Detect and fix encoding
try:
    text = clean.decode("utf-8")
    # Check if it is double encoded
    if "Ã" in text:
        text = clean.decode("latin-1").encode("raw_unicode_escape").decode("utf-8", errors="replace")
except:
    text = clean.decode("latin-1")

# Nuclear clean - replace all the corruption blobs with correct chars
import re

# The corrupted em-dash blob pattern
BLOB = r'[ÃƒÆ\x80-\xff]{4,80}'

def fix_blob(m):
    s = m.group(0)
    # Try to decode as misread utf8
    try:
        return s.encode("latin-1").decode("utf-8")
    except:
        return " - "

text = re.sub(BLOB, fix_blob, text)

with open("templates/contacts/sk_dashboard.html", "w", encoding="utf-8") as f:
    f.write(text)
print("Done")

