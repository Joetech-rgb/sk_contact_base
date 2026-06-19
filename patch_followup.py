import re

with open('templates/contacts/sk_dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

idx = html.find('markSent(this, currentCampPk)')
if idx == -1:
    print('markSent not found')
else:
    # Find the full contact row string to replace
    old = """+'<a href="'+c.wa_link+'" target="_blank" onclick="markSent(this, currentCampPk)" style="display:inline-flex;align-items:center;gap:5px;padding:7px 14px;background:linear-gradient(135deg,#25D366,#128C7E);color:#fff;border-radius:8px;font-size:12px;font-weight:600;text-decoration:none;flex-shrink:0;"><i class="fab fa-whatsapp"></i> Send</div>'"""
    
    new = """+'<div style="display:flex;flex-direction:column;gap:5px;align-items:flex-end;flex-shrink:0;">'
          +'<a href="'+c.wa_link+'" target="_blank" onclick="markSent(this,currentCampPk)" style="display:inline-flex;align-items:center;gap:5px;padding:6px 12px;background:linear-gradient(135deg,#25D366,#128C7E);color:#fff;border-radius:7px;font-size:11px;font-weight:600;text-decoration:none;"><i class="fab fa-whatsapp"></i> Send</a>'
          +'<select class="cc-status-sel" onchange="setCampContactStatus(currentCampPk,'+c.pk+',this.value,this)" style="padding:4px 8px;border:1px solid var(--gray-200);border-radius:6px;font-size:11px;font-family:inherit;cursor:pointer;">'
          +'<option value="pending"'+(c.status==="pending"?" selected":"")+'>Pending</option>'
          +'<option value="interested"'+(c.status==="interested"?" selected":"")+'>Interested</option>'
          +'<option value="not_interested"'+(c.status==="not_interested"?" selected":"")+'>Not Interested</option>'
          +'<option value="confirmed"'+(c.status==="confirmed"?" selected":"")+'>Confirmed</option>'
          +'</select>'
          +'</div>'"""

    if old in html:
        html = html.replace(old, new)
        with open('templates/contacts/sk_dashboard.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print('Patched successfully')
    else:
        print('Pattern not found - exact text around markSent:')
        print(repr(html[idx-100:idx+300]))
