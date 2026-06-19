with open('templates/contacts/sk_dashboard.html', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Extract just the main script block
start = content.find('<script>\n(function(){')
end = content.find('})();\n</script>', start) + 15
script = content[start:end]

# Check for unmatched single quotes in JS string literals  
lines = script.split('\n')
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    # Lines with odd number of single quotes are suspicious
    count = stripped.count("'")
    if count % 2 != 0 and stripped and not stripped.startswith('//') and "don't" not in stripped:
        print(f'ODD QUOTES line {i}: {stripped[:120]}')
