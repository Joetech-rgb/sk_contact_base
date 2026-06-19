# ============================================================
# fix_landing_js.ps1  — fixes the broken IIFE and modal placement
# ============================================================
$ErrorActionPreference = "Stop"
$file = "templates\contacts\landing.html"

$content = Get-Content $file -Raw -Encoding UTF8

# ── 1. Move catChangeModal OUT of <footer> ──────────────────
# The modal is currently sitting inside <footer>...</footer>.
# Remove it from there first, then re-insert it before <footer>.

$modalHtml = @'
<!-- ══ CATEGORY CHANGE REQUEST MODAL ═══════════════════════════ -->
<div class="modal-overlay" id="catChangeModal">
  <div class="modal-box">
    <button class="modal-close" onclick="closePolicy('catChangeModal')" type="button"><i class="fas fa-times"></i></button>
    <div class="modal-title">Change My Category</div>
    <p class="modal-sub">Already registered? Ask the admin to update your category.</p>
    <div class="fw" style="margin-bottom:12px;"><label class="fl">Your WhatsApp Number <span style="color:var(--blue-300);">*</span></label><input type="text" id="ccWhatsapp" placeholder="+233241234567"></div>
    <div class="fw" style="margin-bottom:12px;"><label class="fl">Your Name</label><input type="text" id="ccName" placeholder="Helps the admin find you faster"></div>
    <div class="fw" style="margin-bottom:12px;"><label class="fl">New Category <span style="color:var(--blue-300);">*</span></label><select id="ccCategory"><option value="">-- Select a category --</option>{% for cat in active_categories %}<option value="{{ cat.pk }}">{{ cat.name }}</option>{% endfor %}</select></div>
    <div class="fw" style="margin-bottom:4px;"><label class="fl">Reason (optional)</label><textarea id="ccReason" rows="3" placeholder="Why do you want to change your category?" style="resize:vertical;"></textarea></div>
    <div id="ccMsg" style="display:none;margin-top:10px;padding:10px 14px;border-radius:8px;font-size:13px;font-weight:600;"></div>
    <button class="modal-save" onclick="submitCatChange()" type="button" id="ccSubmitBtn"><i class="fas fa-paper-plane"></i> Submit Request</button>
  </div>
</div>

'@

# Remove the modal from inside footer (wherever it ended up)
$content = $content -replace '(?s)<!-- CATEGORY CHANGE MODAL -->.*?</div>\s*\n</footer>', '</footer>'
$content = $content -replace '(?s)<!-- â•â• CATEGORY CHANGE REQUEST MODAL.*?</div>\s*\n</footer>', '</footer>'

# Insert modal before <footer class="pg-footer">
$content = $content -replace '<footer class="pg-footer">', ($modalHtml + '<footer class="pg-footer">')

# ── 2. Replace the entire {% block extra_js %} section ─────
$cleanJs = @'
{% block extra_js %}
<script>
(function () {
  'use strict';

  /* ── POLICY / GENERAL MODALS ───────────────────────────── */
  window.openPolicy = function(id) {
    var el = document.getElementById(id);
    if (!el) return;
    el.classList.add('open');
    document.body.style.overflow = 'hidden';
  };
  window.closePolicy = function(id) {
    var el = document.getElementById(id);
    if (!el) return;
    el.classList.remove('open');
    document.body.style.overflow = '';
  };

  ['rulesModal','privacyModal','workModal','aboutModal','catChangeModal'].forEach(function(id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('click', function(e) {
      if (e.target === el) closePolicy(id);
    });
  });

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      ['rulesModal','privacyModal','workModal','aboutModal','optModal','catChangeModal'].forEach(function(id) {
        var el = document.getElementById(id);
        if (el && el.classList.contains('open')) {
          el.classList.remove('open');
          document.body.style.overflow = '';
        }
      });
    }
  });

  /* ── NAME FIELD SPLIT ──────────────────────────────────── */
  var fullNameInput = document.getElementById('id_full_name');
  var firstHidden   = document.getElementById('id_first_name_hidden');
  var surnameHidden = document.getElementById('id_surname_hidden');
  if (fullNameInput) {
    fullNameInput.addEventListener('input', function() {
      var parts = this.value.trim().split(/\s+/);
      if (firstHidden)  firstHidden.value  = parts[0] || '';
      if (surnameHidden) surnameHidden.value = parts.slice(1).join(' ') || '';
    });
  }

  /* ── DIAL CODE → COUNTRY ───────────────────────────────── */
  const CODE_TO_COUNTRY = {
    '+233':'Ghana','+234':'Nigeria','+1':'United States','+44':'United Kingdom',
    '+27':'South Africa','+254':'Kenya','+20':'Egypt','+212':'Morocco',
    '+213':'Algeria','+216':'Tunisia','+221':'Senegal','+225':'Ivory Coast',
    '+230':'Mauritius','+231':'Liberia','+232':'Sierra Leone','+235':'Chad',
    '+237':'Cameroon','+241':'Gabon','+242':'Congo','+243':'DR Congo',
    '+244':'Angola','+249':'Sudan','+250':'Rwanda','+251':'Ethiopia',
    '+255':'Tanzania','+256':'Uganda','+260':'Zambia','+263':'Zimbabwe',
    '+265':'Malawi','+267':'Botswana','+268':'Eswatini','+269':'Comoros',
    '+91':'India','+86':'China','+81':'Japan','+61':'Australia',
    '+33':'France','+49':'Germany','+39':'Italy','+34':'Spain',
    '+7':'Russia','+55':'Brazil','+52':'Mexico','+971':'United Arab Emirates',
    '+966':'Saudi Arabia','+355':'Albania','+43':'Austria','+994':'Azerbaijan',
    '+32':'Belgium','+387':'Bosnia and Herzegovina','+359':'Bulgaria',
    '+385':'Croatia','+357':'Cyprus','+420':'Czech Republic','+45':'Denmark',
    '+372':'Estonia','+358':'Finland','+30':'Greece','+36':'Hungary',
    '+354':'Iceland','+353':'Ireland','+972':'Israel','+371':'Latvia',
    '+370':'Lithuania','+352':'Luxembourg','+356':'Malta','+31':'Netherlands',
    '+47':'Norway','+48':'Poland','+351':'Portugal','+40':'Romania',
    '+381':'Serbia','+421':'Slovakia','+386':'Slovenia','+46':'Sweden',
    '+41':'Switzerland','+90':'Turkey','+380':'Ukraine','+82':'South Korea'
  };

  const dialSel        = document.getElementById('id_dial_code');
  const waNumInput     = document.getElementById('id_whatsapp_number');
  const countryFld     = document.getElementById('id_country');
  const countryCodeFld = document.getElementById('id_country_code');
  const phoneErr       = document.getElementById('phoneInlineError');

  function onDialChange() {
    if (!dialSel) return;
    const code = dialSel.value;
    const country = CODE_TO_COUNTRY[code] || '';
    if (countryFld)     countryFld.value     = country;
    if (countryCodeFld) countryCodeFld.value  = code;
  }
  if (dialSel) {
    dialSel.addEventListener('change', onDialChange);
    if (dialSel.value) onDialChange();
  }
  if (countryFld) countryFld.removeAttribute('readonly');

  /* ── FORM SUBMIT ───────────────────────────────────────── */
  const joinForm  = document.getElementById('joinForm');
  const submitBtn = document.getElementById('submitBtn');
  if (joinForm) {
    joinForm.addEventListener('submit', function(e) {
      if (fullNameInput) {
        var parts = fullNameInput.value.trim().split(/\s+/);
        if (firstHidden)  firstHidden.value  = parts[0] || '';
        if (surnameHidden) surnameHidden.value = parts.slice(1).join(' ') || '';
      }
      const code = dialSel ? dialSel.value.trim() : '';
      let rawNum = waNumInput ? waNumInput.value.trim() : '';
      rawNum = rawNum.replace(/[\s\-().]/g, '');
      if (rawNum && /[a-zA-Z]/.test(rawNum)) {
        e.preventDefault();
        if (phoneErr) { phoneErr.textContent = 'Please enter a valid phone number (digits only, no letters).'; phoneErr.style.display = 'block'; }
        if (submitBtn) { submitBtn.classList.remove('loading'); submitBtn.disabled = false; }
        waNumInput.focus(); return;
      }
      if (!code) {
        e.preventDefault();
        if (phoneErr) { phoneErr.textContent = 'Please select a country code for your WhatsApp number.'; phoneErr.style.display = 'block'; }
        if (submitBtn) { submitBtn.classList.remove('loading'); submitBtn.disabled = false; }
        dialSel.focus(); return;
      }
      if (rawNum && !rawNum.startsWith('+')) {
        rawNum = rawNum.replace(/^0+/, '');
        rawNum = code + rawNum;
      }
      const digitsOnly = rawNum.replace('+', '');
      if (rawNum && !/^\d+$/.test(digitsOnly)) {
        e.preventDefault();
        if (phoneErr) { phoneErr.textContent = 'Phone number must contain digits only.'; phoneErr.style.display = 'block'; }
        if (submitBtn) { submitBtn.classList.remove('loading'); submitBtn.disabled = false; }
        waNumInput.focus(); return;
      }
      if (waNumInput)   waNumInput.value   = rawNum;
      if (countryCodeFld && code) countryCodeFld.value = code;
      if (submitBtn) { submitBtn.classList.add('loading'); submitBtn.disabled = true; }
    });
    if (waNumInput && phoneErr) {
      waNumInput.addEventListener('input', function() { phoneErr.style.display = 'none'; phoneErr.textContent = ''; });
    }
  }

  /* ── LEVEL YEAR: digits only ───────────────────────────── */
  const levelFld = document.getElementById('id_level_year');
  if (levelFld) levelFld.addEventListener('input', function() { this.value = this.value.replace(/\D/g, ''); });

  /* ── OPTIONAL MODAL ────────────────────────────────────── */
  const optToggle = document.getElementById('optToggle');
  const optModal  = document.getElementById('optModal');
  const modalClose= document.getElementById('modalClose');
  const modalSave = document.getElementById('modalSave');
  const optSaved  = document.getElementById('optSaved');
  const optIcon   = document.getElementById('optIcon');

  function openModal()  { if(optModal){ optModal.classList.add('open'); document.body.style.overflow='hidden'; } }
  function closeModal() { if(optModal){ optModal.classList.remove('open'); document.body.style.overflow=''; } }

  if (optToggle) {
    optToggle.addEventListener('click', openModal);
    optToggle.addEventListener('keydown', function(e){ if(e.key==='Enter'||e.key===' ') openModal(); });
  }
  if (modalClose) modalClose.addEventListener('click', closeModal);
  if (optModal)   optModal.addEventListener('click', function(e){ if(e.target===optModal) closeModal(); });
  if (modalSave) {
    modalSave.addEventListener('click', function() {
      closeModal();
      if (optSaved)  { optSaved.style.display = 'flex'; }
      if (optToggle) { optToggle.classList.add('done'); }
      if (optIcon)   { optIcon.className = 'fas fa-check'; }
    });
  }

  /* ── SCROLL TO FORM ────────────────────────────────────── */
  const scrollBtn = document.getElementById('scrollToForm');
  if (scrollBtn) {
    scrollBtn.addEventListener('click', function(e) {
      e.preventDefault();
      document.querySelector('.hero-form').scrollIntoView({ behavior:'smooth', block:'start' });
    });
  }

  /* ── FEATURES SLIDESHOW ────────────────────────────────── */
  (function() {
    const track = document.getElementById('ssTrack');
    const dw    = document.getElementById('ssDots');
    const p     = document.getElementById('ssPrev');
    const n     = document.getElementById('ssNext');
    if(!track) return;
    const cards = track.querySelectorAll('.ss-card');
    const vw = window.innerWidth;
    const vc = vw<640?1:vw<960?2:3;
    const total = Math.ceil(cards.length/vc);
    let cur=0, at;
    for(let i=0;i<total;i++){
      const dot = document.createElement('button');
      dot.className = 'ss-dot'+(i===0?' active':'');
      dot.addEventListener('click', function(){ goF(i); });
      dw.appendChild(dot);
    }
    function cw(){ const gap=20,w=track.parentElement.offsetWidth,v=window.innerWidth<640?1:window.innerWidth<960?2:3; return(w-gap*(v-1))/v+gap; }
    function goF(i){ cur=(i+total)%total; track.style.transform='translateX(-'+(cur*vc*cw())+'px)'; dw.querySelectorAll('.ss-dot').forEach(function(d,j){ d.classList.toggle('active',j===cur); }); }
    function ra(){ clearInterval(at); at=setInterval(function(){ goF(cur+1); }, 4500); }
    if(p) p.addEventListener('click', function(){ goF(cur-1); ra(); });
    if(n) n.addEventListener('click', function(){ goF(cur+1); ra(); });
    ra();
    track.addEventListener('mouseenter', function(){ clearInterval(at); });
    track.addEventListener('mouseleave', ra);
  })();

  /* ── SCROLL ANIMATIONS ─────────────────────────────────── */
  const obs = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(e.isIntersecting){
        setTimeout(function(){ e.target.style.opacity='1'; e.target.style.transform='translateY(0)'; }, e.target.dataset.delay||0);
        obs.unobserve(e.target);
      }
    });
  }, {threshold:0.12});
  document.querySelectorAll('.step,.cat,.ti,.fc').forEach(function(el,i){
    el.style.opacity='0'; el.style.transform='translateY(18px)';
    el.style.transition='opacity 0.5s ease,transform 0.5s ease';
    el.dataset.delay=(i%4)*80;
    obs.observe(el);
  });

  /* ── CATEGORY CHANGE REQUEST ───────────────────────────── */
  window.submitCatChange = function() {
    var wa  = (document.getElementById('ccWhatsapp') || {}).value || '';
    var nm  = (document.getElementById('ccName')     || {}).value || '';
    var cat = (document.getElementById('ccCategory') || {}).value || '';
    var rsn = (document.getElementById('ccReason')   || {}).value || '';
    var msg = document.getElementById('ccMsg');
    var btn = document.getElementById('ccSubmitBtn');
    wa = wa.trim(); cat = cat.trim();
    if (!wa || !cat) {
      if (msg) {
        msg.style.cssText = 'display:block;margin-top:10px;padding:10px 14px;border-radius:8px;font-size:13px;font-weight:600;background:#FEE2E2;border:1px solid #FECACA;color:#B91C1C;';
        msg.innerHTML = '<i class="fas fa-exclamation-circle"></i> Please enter your WhatsApp number and select a category.';
      }
      return;
    }
    if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...'; }
    if (msg) { msg.style.display = 'none'; }
    var form = new FormData();
    form.append('whatsapp_number', wa);
    form.append('full_name', nm);
    form.append('requested_category', cat);
    form.append('reason', rsn);
    var csrf = '';
    var ci = document.querySelector('[name=csrfmiddlewaretoken]');
    if (ci) csrf = ci.value;
    fetch('/request-category-change/', { method: 'POST', headers: { 'X-CSRFToken': csrf }, body: form })
      .then(function(r) { return r.json(); })
      .then(function(d) {
        if (msg) {
          if (d.ok) {
            msg.style.cssText = 'display:block;margin-top:10px;padding:10px 14px;border-radius:8px;font-size:13px;font-weight:600;background:#DCFCE7;border:1px solid #BBF7D0;color:#15803D;';
            msg.innerHTML = '<i class="fas fa-check-circle"></i> ' + d.message;
            ['ccWhatsapp','ccName','ccReason'].forEach(function(id) { var el = document.getElementById(id); if (el) el.value = ''; });
            var sel = document.getElementById('ccCategory'); if (sel) sel.value = '';
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-check"></i> Submitted!'; }
          } else {
            msg.style.cssText = 'display:block;margin-top:10px;padding:10px 14px;border-radius:8px;font-size:13px;font-weight:600;background:#FEE2E2;border:1px solid #FECACA;color:#B91C1C;';
            msg.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + (d.error || 'Something went wrong.');
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Request'; }
          }
        }
      })
      .catch(function() {
        if (msg) {
          msg.style.cssText = 'display:block;margin-top:10px;padding:10px 14px;border-radius:8px;font-size:13px;font-weight:600;background:#FEE2E2;border:1px solid #FECACA;color:#B91C1C;';
          msg.innerHTML = '<i class="fas fa-exclamation-circle"></i> Network error. Please try again.';
        }
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Request'; }
      });
  };

})();
</script>
{% endblock %}
'@

# Replace everything from {% block extra_js %} to end of file
$content = $content -replace '(?s)\{% block extra_js %\}.*$', $cleanJs

Set-Content $file $content -Encoding UTF8
Write-Host "Done. Restart server: python manage.py runserver" -ForegroundColor Green
