content = open("templates/contacts/sk_dashboard.html", encoding="utf-8", errors="replace").read()

# Replace ALL corrupted blobs (the long Ãƒ... sequences) with the correct character
import re

# These blobs all represent em-dash or similar
content = re.sub(r'Ãƒ[^\s<>"\']{3,100}', lambda m: {
    True: " - "
}.get(True, " - "), content)

# Fix specific known corruptions that are short
content = content.replace("18 - 24", "18-24")
content = content.replace("25 - 34", "25-34")  
content = content.replace("35 - 44", "35-44")
content = content.replace("45 - 54", "45-54")

# Fix the placeholder text
content = content.replace(
    'placeholder="e.g. Skincare Launch  - June 2026"',
    'placeholder="e.g. Skincare Launch - June 2026"'
)

# Fix title
content = content.replace(
    "<title>Admin Dashboard  - SK Community Base</title>",
    "<title>Admin Dashboard - SK Community Base</title>"
)

# Fix footer
content = content.replace(
    "SK Community Base  - Admin",
    "SK Community Base - Admin"
)

# Fix account links panel label
content = content.replace(
    "Total Link Shares  - All Accounts",
    "Total Link Shares - All Accounts"
)

# Fix WA log
content = content.replace(
    "{% if log.error %}  -  {{ log.error",
    "{% if log.error %} - {{ log.error"
)

# Fix bulk history
content = content.replace(
    "}  - {{ bm.filter_params.category",
    "} - {{ bm.filter_params.category"
)

# Fix date format
content = content.replace(
    'd M Y  -  H:i"',
    'd M Y - H:i"'  
)
content = content.replace(
    "}} - By {{",
    "}} - By {{"
)

# Fix JS strings
content = content.replace(
    "Started  -  +d.message",
    "Started - \"+d.message"
)
content = content.replace(
    "Bulk send complete  -  +d.sent",
    "Bulk send complete - \"+d.sent"
)
content = content.replace(
    "Filtered export  -  +filters",
    "Filtered export - \"+filters"
)

# Fix post author dash
content = content.replace(
    "}}<span class=\"pli-date\"> -  {{ post.author",
    "}}<span class=\"pli-date\"> - {{ post.author"
)

# Fix campaign country dot
content = content.replace("&nbsp; - &nbsp;", "&nbsp;&middot;&nbsp;")

# Fix detail modal defaults
content = content.replace(
    'style="background:var(--gray-50);">  - </div>',
    'style="background:var(--gray-50);">-</div>'
)

# Fix acct handle/followers fallback  
content = content.replace("a.handle|| -  ", "a.handle||'-'")
content = content.replace("a.followers|| -  ", "a.followers||'-'")
content = content.replace("!== -  ") ", "!=='-') ")
content = content.replace("d[map[k]])|| -  ", "d[map[k]])||'-'")

# Fix age range options
content = content.replace("<option>18 - 24</option>", "<option>18-24</option>")
content = content.replace("<option>25 - 34</option>", "<option>25-34</option>")
content = content.replace("<option>35 - 44</option>", "<option>35-44</option>")
content = content.replace("<option>45 - 54</option>", "<option>45-54</option>")

# Fix comment
content = content.replace(
    "{# Clean direct render  -  replaces the messy block above #}",
    "{# Clean direct render - replaces the messy block above #}"
)

with open("templates/contacts/sk_dashboard.html", "w", encoding="utf-8") as f:
    f.write(content)
print("Done!")

