# =============================================================
# S.K Contact Base — Production Patch Script (FIXED)
# Run from the ROOT of your Django project:
#   powershell -ExecutionPolicy Bypass -File apply_patches_fixed.ps1
# =============================================================

param(
    [string]$ProjectRoot = "."
)

$ErrorActionPreference = "Continue"

function Write-OK  { param($m) Write-Host "  [OK]  $m" -ForegroundColor Green }
function Write-FIX { param($m) Write-Host "  [FIX] $m" -ForegroundColor Yellow }
function Write-ERR { param($m) Write-Host "  [ERR] $m" -ForegroundColor Red }
function Write-HDR { param($m) Write-Host "`n==> $m" -ForegroundColor Cyan }

$root = Resolve-Path $ProjectRoot
Write-Host "`nS.K Contact Base — Patch Runner (Fixed)" -ForegroundColor White
Write-Host "Project root: $root`n" -ForegroundColor Gray

function Patch-File {
    param(
        [string]$RelPath,
        [string]$Old,
        [string]$New,
        [string]$Description
    )
    $full = Join-Path $root $RelPath
    if (-not (Test-Path $full)) {
        Write-ERR "File not found: $RelPath  (skipping: $Description)"
        return
    }
    $content = [System.IO.File]::ReadAllText($full, [System.Text.Encoding]::UTF8)
    if ($content.Contains($Old)) {
        $content = $content.Replace($Old, $New)
        [System.IO.File]::WriteAllText($full, $content, [System.Text.Encoding]::UTF8)
        Write-FIX $Description
    } else {
        Write-OK  "$Description (already patched or not found — skipped)"
    }
}

# =============================================================
# PATCH GROUP 1 — bulk.py
# =============================================================
Write-HDR "PATCH GROUP 1: bulk.py"

$bulkCandidates = @(
    "contacts/views/bulk.py",
    "app/views/bulk.py",
    "core/views/bulk.py",
    "contacts/bulk.py"
)
$bulkPath = $null
foreach ($c in $bulkCandidates) {
    if (Test-Path (Join-Path $root $c)) { $bulkPath = $c; break }
}
if (-not $bulkPath) {
    Write-ERR "Cannot locate bulk.py — tried: $($bulkCandidates -join ', ')"
} else {
    Write-OK "Found bulk.py at: $bulkPath"

    # FIX 1-A: move import to module level
    $old1a = @'
def _send_with_retry(contact, template, extra_params, retries=3, delay=8, language="en"):
    """
    Attempt send_whatsapp up to `retries` times.
    - ConnectionError / network failures  → retry after `delay` seconds
    - False return from send_whatsapp     → do NOT retry (API-level rejection)
    Returns True on success, False on final failure.
    """
    from ..services.whatsapp import send_whatsapp

    for attempt in range(1, retries + 1):
        try:
            params = extra_params
            if template == "sk_opportunity" and not params:
                params = [contact.first_name]

            result = send_whatsapp(
'@
    $new1a = @'
from ..services.whatsapp import send_whatsapp  # module-level import (patched)


def _send_with_retry(contact, template, extra_params, retries=3, delay=8, language="en"):
    """
    Attempt send_whatsapp up to `retries` times.
    - ConnectionError / network failures  → retry after `delay` seconds
    - False return from send_whatsapp     → do NOT retry (API-level rejection)
    Returns True on success, False on final failure.
    """
    for attempt in range(1, retries + 1):
        try:
            params = extra_params
            if template == "sk_opportunity" and not params:
                params = [contact.first_name]

            result = send_whatsapp(
'@
    Patch-File $bulkPath $old1a $new1a "Move send_whatsapp import to module level"

    # FIX 1-B: compose view lock
    $old1b = @'
        # FIX: daemon=False — thread survives worker recycles
        t = threading.Thread(
            target=_do_bulk_send,
            args=(bulk.pk, contact_ids, template, extra_params),
            daemon=False,
        )
        t.start()
'@
    $new1b = @'
        # PATCHED: wrap with lock acquire/release so compose view
        # cannot run concurrently with the API send view
        def _compose_run_and_release():
            if _bulk_send_lock.acquire(blocking=True, timeout=5):
                try:
                    _do_bulk_send(bulk.pk, contact_ids, template, extra_params)
                finally:
                    _bulk_send_lock.release()
            else:
                import logging
                logging.getLogger(__name__).warning(
                    "[Bulk Send] Could not acquire lock for compose view — send skipped."
                )

        t = threading.Thread(target=_compose_run_and_release, daemon=False)
        t.start()
'@
    Patch-File $bulkPath $old1b $new1b "bulk_compose_view: add lock acquire to prevent race"

    # FIX 1-C: save progress more frequently
    $old1c = @'
        # Persist progress every 10 messages
        if (sent + failed) % 10 == 0:
            BulkMessage.objects.filter(pk=bulk_id).update(
                sent_count=sent,
                failed_count=failed,
            )
'@
    $new1c = @'
        # PATCHED: save every message for small sends, every 10 for large
        _total_so_far = sent + failed
        _save_interval = 1 if len(contact_ids) <= 50 else 10
        if _total_so_far % _save_interval == 0:
            BulkMessage.objects.filter(pk=bulk_id).update(
                sent_count=sent,
                failed_count=failed,
            )
'@
    Patch-File $bulkPath $old1c $new1c "Save progress more frequently for small bulk sends"

    # FIX 1-D: language default en -> en_US
    $old1d = 'def _do_bulk_send(bulk_id, contact_ids, template, extra_params=None, language="en"):'
    $new1d = 'def _do_bulk_send(bulk_id, contact_ids, template, extra_params=None, language="en_US"):'
    Patch-File $bulkPath $old1d $new1d "Default language to en_US"

    $old1e = '        language = data.get("language", "en")'
    $new1e = '        language = data.get("language", "en_US")  # PATCHED: was "en"'
    Patch-File $bulkPath $old1e $new1e "bulk_send_api: default language en -> en_US"

    # FIX 1-E: bulk_preview_api accept age_range
    $old1f = @'
def bulk_preview_api(request):
    qs       = Contact.objects.all()
    category = request.GET.get("category", "").strip()
    country  = request.GET.get("country",  "").strip()
    platform = request.GET.get("platform", "").strip()
    if category: qs = qs.filter(category__name__iexact=category)
    if country:  qs = qs.filter(country__iexact=country)
    if platform: qs = qs.filter(platform__iexact=platform)
    return JsonResponse({"count": qs.count()})
'@
    $new1f = @'
def bulk_preview_api(request):
    qs        = Contact.objects.all()
    category  = request.GET.get("category",  "").strip()
    country   = request.GET.get("country",   "").strip()
    platform  = request.GET.get("platform",  "").strip()
    age_range = request.GET.get("age_range", "").strip()  # PATCHED
    if category:  qs = qs.filter(category__name__iexact=category)
    if country:   qs = qs.filter(country__iexact=country)
    if platform:  qs = qs.filter(platform__iexact=platform)
    if age_range: qs = qs.filter(age_range__iexact=age_range)  # PATCHED
    return JsonResponse({"count": qs.count()})
'@
    Patch-File $bulkPath $old1f $new1f "bulk_preview_api: accept and apply age_range filter"

    # FIX 1-F: bulk_send_api accept age_range
    $old1g = @'
        category     = data.get("category", "").strip()
        country      = data.get("country",  "").strip()
        platform     = data.get("platform", "").strip()
        extra_params = data.get("params", [])
        if not isinstance(extra_params, list):
            extra_params = []
        language = data.get("language", "en_US")  # PATCHED: was "en"

        qs = Contact.objects.all()
        if category: qs = qs.filter(category__name__iexact=category)
        if country:  qs = qs.filter(country__iexact=country)
        if platform: qs = qs.filter(platform__iexact=platform)
'@
    $new1g = @'
        category     = data.get("category",  "").strip()
        country      = data.get("country",   "").strip()
        platform     = data.get("platform",  "").strip()
        age_range    = data.get("age_range", "").strip()  # PATCHED
        extra_params = data.get("params", [])
        if not isinstance(extra_params, list):
            extra_params = []
        language = data.get("language", "en_US")  # PATCHED: was "en"

        qs = Contact.objects.all()
        if category:  qs = qs.filter(category__name__iexact=category)
        if country:   qs = qs.filter(country__iexact=country)
        if platform:  qs = qs.filter(platform__iexact=platform)
        if age_range: qs = qs.filter(age_range__iexact=age_range)  # PATCHED
'@
    Patch-File $bulkPath $old1g $new1g "bulk_send_api: accept and apply age_range filter"
}


# =============================================================
# PATCH GROUP 2 — base_dashboard.html
# =============================================================
Write-HDR "PATCH GROUP 2: base_dashboard.html"

$dashCandidates = @(
    "templates/contacts/base_dashboard.html",
    "templates/base_dashboard.html",
    "contacts/templates/contacts/base_dashboard.html",
    "templates/dashboard.html"
)
$dashPath = $null
foreach ($c in $dashCandidates) {
    if (Test-Path (Join-Path $root $c)) { $dashPath = $c; break }
}
if (-not $dashPath) {
    Write-ERR "Cannot locate base_dashboard.html"
} else {
    Write-OK "Found dashboard at: $dashPath"

    # FIX 2-A: widthratio division by zero
    $old2a = '{% else %}<span class="bhi-stat bhi-rate-s">{% if bm.sent_count %}{% widthratio bm.sent_count bm.sent_count|add:bm.failed_count 100 %}%{% else %}0%{% endif %}</span>{% endif %}'
    $new2a = '{% else %}<span class="bhi-stat bhi-rate-s">{% if bm.sent_count and bm.failed_count %}{% widthratio bm.sent_count bm.sent_count|add:bm.failed_count 100 %}%{% elif bm.sent_count %}100%{% else %}0%{% endif %}</span>{% endif %}'
    Patch-File $dashPath $old2a $new2a "Fix widthratio division by zero"

    # FIX 2-B: chart JSON try/catch
    $old2b = @"
      labels:{{ chart_labels_json|safe }},
      datasets:[{
        label:'Registrations',
        data:{{ chart_values_json|safe }},
"@
    $new2b = @"
      labels:(function(){try{return {{ chart_labels_json|safe }};}catch(e){return [];}}()),
      datasets:[{
        label:'Registrations',
        data:(function(){try{return {{ chart_values_json|safe }};}catch(e){return [];}}()),
"@
    Patch-File $dashPath $old2b $new2b "Wrap chart JSON in try/catch"

    # FIX 2-C: null whatsapp_number guard
    $old2c = @"
      if(waLink && d.whatsapp_number){
        var clean = d.whatsapp_number.replace(/\D/g,'');
"@
    $new2c = @"
      if(waLink && d.whatsapp_number){
        var clean = (d.whatsapp_number||'').replace(/\D/g,'');
"@
    Patch-File $dashPath $old2c $new2c "Guard against null whatsapp_number"

    # FIX 2-D: null c.name guard
    $old2d = "+'<div style=""width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,var(--blue-400),var(--blue-500));display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;flex-shrink:0;"">'+c.name.substring(0,2).toUpperCase()+'</div>'"
    $new2d = "+'<div style=""width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,var(--blue-400),var(--blue-500));display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;flex-shrink:0;"">'+((c.name||'??').substring(0,2).toUpperCase())+'</div>'"
    Patch-File $dashPath $old2d $new2d "Guard against null c.name in campaign contacts"

    # FIX 2-E: Today preset sets both dates
    $old2e = "    if(preset==='today' && dfEl){ dfEl.value=toDate; }"
    $new2e = "    if(preset==='today'){ if(dfEl) dfEl.value=toDate; if(dtEl) dtEl.value=toDate; }"
    Patch-File $dashPath $old2e $new2e "Fix Today preset: set both dateFrom and dateTo"

    # FIX 2-F: include age_range in bulk send body
    $old2f = @"
  fetch('/api/bulk/send/', {
    method:'POST',
    headers:{'Content-Type':'application/json','X-CSRFToken':CSRF},
    body:JSON.stringify({template:template, category:category, country:country, platform:platform, params:[], language: template==='sk_welcome' ? 'en_US' : 'en'})
"@
    $new2f = @"
  var age = (document.getElementById('bsAge')||{}).value||'';
  fetch('/api/bulk/send/', {
    method:'POST',
    headers:{'Content-Type':'application/json','X-CSRFToken':CSRF},
    body:JSON.stringify({template:template, category:category, country:country, platform:platform, age_range:age, params:[], language: template==='sk_welcome' ? 'en_US' : 'en_US'})
"@
    Patch-File $dashPath $old2f $new2f "Include age_range in bulk send POST body"

    # FIX 2-G: include age_range in preview fetch
    $old2g = @"
window.bsUpdatePreview = function(){
  var cat = (document.getElementById('bsCategory')||{}).value||'';
  var cou = (document.getElementById('bsCountry')||{}).value||'';
  var pla = (document.getElementById('bsPlatform')||{}).value||'';
  var p = new URLSearchParams();
  if(cat) p.set('category',cat);
  if(cou) p.set('country',cou);
  if(pla) p.set('platform',pla);
"@
    $new2g = @"
window.bsUpdatePreview = function(){
  var cat = (document.getElementById('bsCategory')||{}).value||'';
  var age = (document.getElementById('bsAge')||{}).value||'';
  var cou = (document.getElementById('bsCountry')||{}).value||'';
  var pla = (document.getElementById('bsPlatform')||{}).value||'';
  var p = new URLSearchParams();
  if(cat) p.set('category',cat);
  if(age) p.set('age_range',age);
  if(cou) p.set('country',cou);
  if(pla) p.set('platform',pla);
"@
    Patch-File $dashPath $old2g $new2g "Include age_range in bulk preview fetch"

    # FIX 2-H: pollBulkStatus guard null querySelector
    $old2h = @"
        var row = document.getElementById('bulk-row-'+bulkId);
        if(row){
          row.querySelector('.bhi-title').textContent = 'Sending... '+d.sent+' sent, '+d.failed+' failed';
        }
        if(d.status==='done'){ clearInterval(interval); toast('Bulk send complete -   -  '+d.sent+' sent!'); }
"@
    $new2h = @"
        var row = document.getElementById('bulk-row-'+bulkId);
        if(row){
          var titleEl = row.querySelector('.bhi-title');
          if(titleEl) titleEl.textContent = 'Sending... '+d.sent+' sent, '+d.failed+' failed';
        }
        if(d.status==='done'){ clearInterval(interval); toast('Bulk send complete — '+d.sent+' sent!'); }
"@
    Patch-File $dashPath $old2h $new2h "Guard querySelector null in pollBulkStatus"

    # FIX 2-I: add filterModal HTML if missing
    $dashFull = Join-Path $root $dashPath
    $dashContent = [System.IO.File]::ReadAllText($dashFull, [System.Text.Encoding]::UTF8)
    if (-not $dashContent.Contains('id="filterModal"')) {
        $filterModalHtml = @'

<!-- PATCHED: filterModal was missing -->
<div class="modal-overlay" id="filterModal">
  <div class="modal-box">
    <button class="modal-close" onclick="closeModal('filterModal')"><i class="fas fa-times"></i></button>
    <div class="modal-title">Filter Contacts</div>
    <p class="modal-sub">Narrow down the contacts list by category, country, or platform.</p>
    <form method="get" id="filterModalForm">
      <input type="hidden" name="tab" value="contacts">
      <div class="fw">
        <label class="fl">Category</label>
        <select class="fi fi-select" name="f_cat">
          <option value="">All Categories</option>
          {% for cat in categories %}
          <option value="{{ cat.name }}" {% if f_cat == cat.name %}selected{% endif %}>{{ cat.name }}</option>
          {% endfor %}
        </select>
      </div>
      <div class="fw">
        <label class="fl">Country</label>
        <select class="fi fi-select" name="f_country">
          <option value="">All Countries</option>
          {% for c in country_list %}
          <option value="{{ c }}" {% if f_country == c %}selected{% endif %}>{{ c }}</option>
          {% endfor %}
        </select>
      </div>
      <div class="fw">
        <label class="fl">Platform</label>
        <select class="fi fi-select" name="f_platform">
          <option value="">All Platforms</option>
          {% for plat in platform_stats %}
          <option value="{{ plat.platform }}" {% if f_platform == plat.platform %}selected{% endif %}>{{ plat.platform|title }}</option>
          {% endfor %}
        </select>
      </div>
      <div style="display:flex;gap:10px;margin-top:4px;">
        <button type="submit" class="modal-save" style="flex:1;"><i class="fas fa-filter"></i> Apply Filter</button>
        <a href="?tab=contacts" class="modal-save" style="flex:0 0 auto;width:auto;padding:10px 18px;background:var(--gray-100);color:var(--gray-600);box-shadow:none;"><i class="fas fa-times"></i> Clear</a>
      </div>
    </form>
  </div>
</div>
'@
        $dashContent = $dashContent.Replace('</body>', $filterModalHtml + '</body>')
        [System.IO.File]::WriteAllText($dashFull, $dashContent, [System.Text.Encoding]::UTF8)
        Write-FIX "Added missing filterModal HTML"
    } else {
        Write-OK "filterModal already exists — skipped"
    }

    # FIX 2-J: escape post title/content (XSS)
    $old2j = @"
          +'<div class=""pli-info""><div class=""pli-title"">'+d.title+'</div>'
          +'<div class=""pli-body"">'+d.content+'</div>'
"@
    $new2j = @"
          +'<div class=""pli-info""><div class=""pli-title"">'+_esc(d.title)+'</div>'
          +'<div class=""pli-body"">'+_esc(d.content)+'</div>'
"@
    Patch-File $dashPath $old2j $new2j "Escape post title/content before innerHTML"

    # FIX 2-K: add _esc helper
    $old2k = "var CSRF = '{{ csrf_token }}';"
    $new2k = @"
var CSRF = '{{ csrf_token }}';

// PATCHED: HTML escape helper
function _esc(s){
  if(!s) return '';
  return String(s)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/'/g,'&#39;')
    .replace(/`/g,'&#96;');
}
"@
    Patch-File $dashPath $old2k $new2k "Add _esc() HTML escape helper"

    # FIX 2-L: saveCampaignCounts — single atomic request
    $old2l = @"
window.saveCampaignCounts = function(id){
  var contacted = document.getElementById('inp-contacted-'+id).value;
  var responded = document.getElementById('inp-responded-'+id).value;
  var confirmed = document.getElementById('inp-confirmed-'+id).value;
  function upd(field, value, cb){
    var form = new FormData();
    form.append('field', field); form.append('value', value);
    return fetch('/dashboard/campaign/'+id+'/update/', {method:'POST', headers:{'X-CSRFToken':CSRF}, body:form})
      .then(function(r){ return r.json(); })
      .then(function(d){ if(cb) cb(d); return d; });
  }
  upd('contacted_count', contacted)
    .then(function(){ return upd('responded_count', responded); })
    .then(function(){ return upd('confirmed_count', confirmed); })
    .then(function(d){
      if(d.ok){
        document.getElementById('camp-rr-'+id).innerHTML = d.response_rate+'<span style=""font-size:13px;"">%</span>';
        document.getElementById('camp-cr-'+id).innerHTML = d.conversion_rate+'<span style=""font-size:13px;"">%</span>';
        var bar = document.querySelector('#camp-'+id+' .campaign-progress-fill');
        if(bar) bar.style.width = d.response_rate+'%';
        toast('Campaign updated!');
      }
    });
};
"@
    $new2l = @"
// PATCHED: single atomic POST for all three counts
window.saveCampaignCounts = function(id){
  var contacted = document.getElementById('inp-contacted-'+id).value;
  var responded = document.getElementById('inp-responded-'+id).value;
  var confirmed = document.getElementById('inp-confirmed-'+id).value;
  var form = new FormData();
  form.append('field', 'bulk_counts');
  form.append('contacted_count', contacted);
  form.append('responded_count', responded);
  form.append('confirmed_count', confirmed);
  fetch('/dashboard/campaign/'+id+'/update/', {method:'POST', headers:{'X-CSRFToken':CSRF}, body:form})
    .then(function(r){ return r.json(); })
    .then(function(d){
      if(d.ok){
        document.getElementById('camp-rr-'+id).innerHTML = d.response_rate+'<span style=""font-size:13px;"">%</span>';
        document.getElementById('camp-cr-'+id).innerHTML = d.conversion_rate+'<span style=""font-size:13px;"">%</span>';
        var bar = document.querySelector('#camp-'+id+' .campaign-progress-fill');
        if(bar) bar.style.width = d.response_rate+'%';
        toast('Campaign updated!');
      } else { toast(d.error||'Save failed','error'); }
    })
    .catch(function(){ toast('Network error saving counts','error'); });
};
"@
    Patch-File $dashPath $old2l $new2l "saveCampaignCounts: single atomic request"
}


# =============================================================
# PATCH GROUP 3 — landing.html
# =============================================================
Write-HDR "PATCH GROUP 3: landing.html"

$landingCandidates = @(
    "templates/contacts/landing.html",
    "templates/landing.html",
    "contacts/templates/contacts/landing.html"
)
$landingPath = $null
foreach ($c in $landingCandidates) {
    if (Test-Path (Join-Path $root $c)) { $landingPath = $c; break }
}
if (-not $landingPath) {
    Write-ERR "Cannot locate landing.html"
} else {
    Write-OK "Found landing.html at: $landingPath"

    $old3a = "  'use strict';"
    $new3a = @"
  'use strict';

  /* PATCHED: toggleLang was called but never defined */
  var _currentLang = 'en';
  window.toggleLang = function(){
    _currentLang = _currentLang === 'en' ? 'fr' : 'en';
    var flag  = document.getElementById('langFlag');
    var label = document.getElementById('langLabel');
    if(_currentLang === 'fr'){
      if(flag)  flag.innerHTML  = '&#x1F1EB;&#x1F1F7;';
      if(label) label.textContent = 'FR';
    } else {
      if(flag)  flag.innerHTML  = '&#x1F1EC;&#x1F1E7;';
      if(label) label.textContent = 'EN';
    }
  };
"@
    Patch-File $landingPath $old3a $new3a "Add toggleLang() definition"

    $landingFull = Join-Path $root $landingPath
    $lContent = [System.IO.File]::ReadAllText($landingFull, [System.Text.Encoding]::UTF8)
    if ($lContent.Contains('233XXXXXXXXX')) {
        Write-ERR "MANUAL ACTION REQUIRED: Replace '233XXXXXXXXX' in $landingPath with the real WhatsApp number."
    } else {
        Write-OK "No placeholder WhatsApp number found"
    }
}


# =============================================================
# PATCH GROUP 4 — campaign update view (bulk_counts)
# =============================================================
Write-HDR "PATCH GROUP 4: campaign update view (bulk_counts field)"

$viewFiles = Get-ChildItem -Path $root -Recurse -Filter "*.py" | Where-Object {
    $_.FullName -notmatch "migrations" -and
    $_.FullName -notmatch "__pycache__" -and
    (Select-String -Path $_.FullName -Pattern "campaign.*update|update.*campaign" -Quiet)
}

if ($viewFiles.Count -eq 0) {
    Write-ERR "Cannot auto-locate campaign update view — apply GROUP 4 manually."
} else {
    foreach ($vf in $viewFiles) {
        $rel = $vf.FullName.Substring($root.ToString().Length + 1)
        Write-OK "Checking: $rel"

        $old4a = @"
    field = form.get('field','')
    value = form.get('value','')
"@
        $new4a = @"
    field = form.get('field','')
    value = form.get('value','')

    # PATCHED: atomic bulk_counts update from saveCampaignCounts JS
    if field == 'bulk_counts':
        try:
            camp.contacted_count = int(form.get('contacted_count', camp.contacted_count))
            camp.responded_count = int(form.get('responded_count', camp.responded_count))
            camp.confirmed_count = int(form.get('confirmed_count', camp.confirmed_count))
            camp.save(update_fields=['contacted_count','responded_count','confirmed_count'])
            return JsonResponse({
                'ok': True,
                'response_rate': camp.response_rate,
                'conversion_rate': camp.conversion_rate,
            })
        except (ValueError, TypeError) as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)
"@
        Patch-File $rel $old4a $new4a "Add bulk_counts atomic handler in campaign update view"
    }
}


# =============================================================
# SUMMARY
# =============================================================
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  PATCH RUN COMPLETE" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host @"

AUTOMATIC FIXES APPLIED:
  [1] bulk.py  — send_whatsapp import moved to module level
  [1] bulk.py  — compose view now acquires lock (race condition fixed)
  [1] bulk.py  — progress saved more frequently for small sends
  [1] bulk.py  — language default changed to en_US
  [1] bulk.py  — bulk_preview_api accepts age_range
  [1] bulk.py  — bulk_send_api accepts age_range
  [2] dashboard — widthratio division-by-zero fixed
  [2] dashboard — chart JSON wrapped in try/catch
  [2] dashboard — null whatsapp_number guard
  [2] dashboard — null c.name guard in campaign contacts
  [2] dashboard — Today preset sets both from AND to date
  [2] dashboard — age_range in bulk preview + send
  [2] dashboard — filterModal HTML added if missing
  [2] dashboard — _esc() helper added, innerHTML XSS fixed
  [2] dashboard — saveCampaignCounts single atomic request
  [2] dashboard — pollBulkStatus querySelector null guard
  [3] landing   — toggleLang() stub added
  [4] views     — bulk_counts atomic handler added

MANUAL ACTIONS STILL REQUIRED:
  [M1] Replace '233XXXXXXXXX' in landing.html with your real WhatsApp number
  [M2] Add prefetch_related to campaigns query in dashboard view:
         campaigns = Campaign.objects.prefetch_related('target_categories').order_by('-created_at')
  [M3] Verify Contact model has: whatsapp_chat_url, handle_clean, platform_profile_url
  [M4] Verify /request-category-change/ is in urls.py
  [M5] Confirm dashboard view passes: categories, country_list, platform_stats, f_cat, f_country, f_platform
  [M6] For multi-worker Gunicorn, replace _bulk_send_lock with Redis/redlock
  [M7] openAllWaLinks() — browsers block >3 tabs; use Copy Numbers for large campaigns

"@ -ForegroundColor Gray

Write-Host "Run: python manage.py check" -ForegroundColor Yellow
Write-Host "Run: python manage.py test`n" -ForegroundColor Yellow
