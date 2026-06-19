with open('templates/contacts/sk_dashboard.html', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'a.handle||' in line or 'a.followers||' in line:
        print(f'LINE {i}:')
        print(repr(line))
        print()
