import re

with open(r'templates\contacts\sk_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''d.contacts.forEach(function(c){
        campWaLinks.push(c.wa_link);
        campNumbers.push(c.number);
        list.innerHTML += '<div style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:var(--white);border:1px solid var(--blue-100);border-radius:8px;">'
          +'<div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,var(--blue-400),var(--blue-500));display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;flex-shrink:0;">'+c.name.substring(0,2).toUpperCase()+'</div>'
          +'<div style="flex:1;min-width:0;">'
          +'<div style="font-size:13px;font-weight:700;color:var(--blue-900);">'+c.name+'</div>'
          +'<div style="font-size:11px;color:var(--gray-400);">'+c.number+' &bull; '+c.category+'</div>'
          +'</div>'
          +'<div style="display:flex;flex-direction:column;gap:5px;align-items:flex-end;flex-shrink:0;">'
          +'<a href="'+c.wa_link+'" target="_blank" onclick="markSent(this,currentCampPk)" style="display:inline-flex;align-items:center;gap:5px;padding:6px 12px;background:linear-gradient(135deg,#25D366,#128C7E);color:#fff;border-radius:7px;font-size:11px;font-weight:600;text-decoration:none;"><i class="fab fa-whatsapp"></i> Send</a>'
          +'<select class="cc-status-sel" onchange="setCampContactStatus(currentCampPk,'+c.pk+',this.value,this)" style="padding:4px 8px;border:1px solid var(--gray-200);border-radius:6px;font-size:11px;font-family:inherit;cursor:pointer;">'
          +'<option value="pending"'+(c.status==="pending"?" selected":"")+'>Pending</option>'
          +'<option value="interested"'+(c.status==="interested"?" selected":"")+'>Interested</option>'
          +'<option value="not_interested"'+(c.status==="not_interested"?" selected":"")+'>Not Interested</option>'
          +'<option value="confirmed"'+(c.status==="confirmed"?" selected":"")+'>Confirmed</option>'
          +'</select>'
          +'</div>'
          +'</div>';
      });'''

new = '''d.contacts.forEach(function(c){
        campWaLinks.push(c.wa_link);
        campNumbers.push(c.number);
        var row = document.createElement('div');
        row.className = 'cc-row';
        row.style.cssText = 'display:flex;align-items:center;gap:12px;padding:10px 14px;background:var(--white);border:1px solid var(--blue-100);border-radius:8px;';
        row.innerHTML =
          '<div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,var(--blue-400),var(--blue-500));display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;flex-shrink:0;">'+c.name.substring(0,2).toUpperCase()+'</div>'
          +'<div style="flex:1;min-width:0;">'
          +'<div style="font-size:13px;font-weight:700;color:var(--blue-900);">'+c.name+'</div>'
          +'<div style="font-size:11px;color:var(--gray-400);">'+c.number+' &bull; '+c.category+'</div>'
          +'</div>'
          +'<div style="display:flex;flex-direction:column;gap:5px;align-items:flex-end;flex-shrink:0;">'
          +'<a href="'+c.wa_link+'" target="_blank" style="display:inline-flex;align-items:center;gap:5px;padding:6px 12px;background:linear-gradient(135deg,#25D366,#128C7E);color:#fff;border-radius:7px;font-size:11px;font-weight:600;text-decoration:none;"><i class="fab fa-whatsapp"></i> Send</a>'
          +'<select class="cc-status-sel" style="padding:4px 8px;border:1px solid var(--gray-200);border-radius:6px;font-size:11px;font-family:inherit;cursor:pointer;">'
          +'<option value="pending"'+(c.status==="pending"?" selected":"")+'>Pending</option>'
          +'<option value="interested"'+(c.status==="interested"?" selected":"")+'>Interested</option>'
          +'<option value="not_interested"'+(c.status==="not_interested"?" selected":"")+'>Not Interested</option>'
          +'<option value="confirmed"'+(c.status==="confirmed"?" selected":"")+'>Confirmed</option>'
          +'</select>'
          +'</div>';
        var sel = row.querySelector('.cc-status-sel');
        (function(contactPk, campPk, selectEl){
          selectEl.addEventListener('change', function(){
            setCampContactStatus(campPk, contactPk, this.value, this);
          });
        })(c.pk, pk, sel);
        var sendLink = row.querySelector('a');
        sendLink.addEventListener('click', function(){
          row.style.opacity = '0.45';
          this.innerHTML = '<i class="fas fa-check"></i> Sent';
          this.style.background = 'var(--green-50)';
          this.style.color = 'var(--green-700)';
        });
        list.appendChild(row);
      });'''

if old in content:
    content = content.replace(old, new)
    with open(r'templates\contacts\sk_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patched successfully')
else:
    print('Pattern not found - exact text around forEach:')
    idx = content.find('campWaLinks.push(c.wa_link)')
    print(repr(content[idx-20:idx+500]))
