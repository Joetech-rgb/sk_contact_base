with open('templates/contacts/sk_dashboard.html', encoding='utf-8', errors='replace') as f:
    content = f.read()

import re

# Find the IIFE opening and check for syntax issues before setTab
iife_start = content.find("(function(){")
iife_end = content.find("})();", iife_start)
iife = content[iife_start:iife_start+3000]

# Look for unmatched quotes or corruption inside JS
lines = iife.split('\n')
for i, line in enumerate(lines, 1):
    if ' - ' in line and ('||' in line or '!==' in line or 'textContent' in line):
        print(f'SUSPICIOUS line {i}: {line[:120]}')
    if 'Ã' in line or '\ufffd' in line:
        print(f'CORRUPT line {i}: {line[:120]}')
