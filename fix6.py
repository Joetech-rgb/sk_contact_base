import re

with open('templates/contacts/sk_dashboard.html', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Replace all corrupted blobs with dash
content = re.sub(r'Ãƒ[^\s<>"]{2,150}', ' - ', content)

# Clean up double spaces left behind
content = content.replace('  - ', ' - ')

# Fix age range options (corruption left spaces around hyphens)
for pair in [('18 - 24','18-24'),('25 - 34','25-34'),('35 - 44','35-44'),('45 - 54','45-54')]:
    content = content.replace(pair[0], pair[1])

# Fix JS fallback strings
content = content.replace("a.handle|| - ", "a.handle||'-'")
content = content.replace("a.followers|| - ", "a.followers||'-'")
content = content.replace("!== - ') ", "!=='-') ")
content = content.replace("d[map[k]])|| - ", "d[map[k]])||'-'")

# Fix specific visible text
content = content.replace('Total Link Shares - All Accounts', 'Total Link Shares - All Accounts')
content = content.replace('S.K Contact Base - Admin', 'S.K Contact Base - Admin')
content = content.replace('<title>Admin Dashboard - S.K Contact Base</title>', '<title>Admin Dashboard - S.K Contact Base</title>')

# Fix bulk send JS messages  
content = content.replace("'Started - '+d.message", "'Started - '+d.message")
content = content.replace("'Bulk send complete - '+d.sent+' sent!'", "'Bulk send complete - '+d.sent+' sent!'")
content = content.replace("'Filtered export - '+filters.join(', ')", "'Filtered export - '+filters.join(', ')")

# Fix date format in template
content = content.replace('d M Y - H:i"', 'd M Y, H:i"')

# Fix middot for campaign country separator
content = content.replace('&nbsp; - &nbsp;', '&nbsp;&middot;&nbsp;')

# Fix detail modal placeholder dashes
content = re.sub(r'style="background:var\(--gray-50\);"> - </div>', 'style="background:var(--gray-50);">-</div>', content)

with open('templates/contacts/sk_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
