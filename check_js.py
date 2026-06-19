with open('templates/contacts/sk_dashboard.html', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find where setTab is defined
idx = content.find('window.setTab')
if idx >= 0:
    print('FOUND setTab at char', idx)
    print(content[idx:idx+500])
else:
    print('setTab NOT FOUND in file')

# Check tab-panel exists
import re
panels = re.findall(r'id="panel-(\w+[-\w]*)"', content)
print('Panels found:', panels)

# Check for syntax errors near setTab
idx2 = content.find("window.setTab('analytics')")
print('Init call found:', idx2 > 0)
