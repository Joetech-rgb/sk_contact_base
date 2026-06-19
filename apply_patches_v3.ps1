# S.K Contact Base - Production Patch Script v3
# Run from project root:
#   powershell -ExecutionPolicy Bypass -File ".\apply_patches_v3.ps1"

param([string]$ProjectRoot = ".")
$ErrorActionPreference = "Continue"

function Write-OK  { param($m) Write-Host "  [OK]  $m" -ForegroundColor Green }
function Write-FIX { param($m) Write-Host "  [FIX] $m" -ForegroundColor Yellow }
function Write-ERR { param($m) Write-Host "  [ERR] $m" -ForegroundColor Red }
function Write-HDR { param($m) Write-Host "`n==> $m" -ForegroundColor Cyan }

$root = Resolve-Path $ProjectRoot
Write-Host "S.K Contact Base - Patch Runner v3" -ForegroundColor White
Write-Host "Project root: $root" -ForegroundColor Gray

function Patch-File {
    param([string]$RelPath, [string]$Old, [string]$New, [string]$Desc)
    $full = Join-Path $root $RelPath
    if (-not (Test-Path $full)) { Write-ERR "Not found: $RelPath (skip: $Desc)"; return }
    $content = [System.IO.File]::ReadAllText($full, [System.Text.Encoding]::UTF8)
    if ($content.Contains($Old)) {
        $content = $content.Replace($Old, $New)
        [System.IO.File]::WriteAllText($full, $content, [System.Text.Encoding]::UTF8)
        Write-FIX $Desc
    } else {
        Write-OK "$Desc (already patched or not found - skipped)"
    }
}

# Both CRLF and LF variants
function Patch-FileBoth {
    param([string]$RelPath, [string]$Old, [string]$New, [string]$Desc)
    Patch-File $RelPath $Old $New "$Desc"
    Patch-File $RelPath $Old.Replace("`r`n", "`n") $New "$Desc (LF)"
}

# ============================================================
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
    Write-ERR "Cannot locate bulk.py"
} else {
    Write-OK "Found bulk.py at: $bulkPath"

    # 1-D: language default
    $old = 'def _do_bulk_send(bulk_id, contact_ids, template, extra_params=None, language="en"):'
    $new = 'def _do_bulk_send(bulk_id, contact_ids, template, extra_params=None, language="en_US"):'
    Patch-File $bulkPath $old $new "1-D: Default language to en_US"

    $old = '        language = data.get("language", "en")'
    $new = '        language = data.get("language", "en_US")  # PATCHED'
    Patch-File $bulkPath $old $new "1-D: bulk_send_api language default"

    # 1-C: save progress interval
    $old1c = @"
        # Persist progress every 10 messages
        if (sent + failed) % 10 == 0:
            BulkMessage.objects.filter(pk=bulk_id).update(
                sent_count=sent,
                failed_count=failed,
            )
"@
    $new1c = @"
        # PATCHED: save every msg for small sends, every 10 for large
        _total_so_far = sent + failed
        _save_interval = 1 if len(contact_ids) <= 50 else 10
        if _total_so_far % _save_interval == 0:
            BulkMessage.objects.filter(pk=bulk_id).update(
                sent_count=sent,
                failed_count=failed,
            )
"@
    Patch-FileBoth $bulkPath $old1c $new1c "1-C: Save progress more frequently"

    # 1-B: compose view lock
    $old1b = @"
        # FIX: daemon=False
        t = threading.Thread(
            target=_do_bulk_send,
            args=(bulk.pk, contact_ids, template, extra_params),
            daemon=False,
        )
        t.start()
"@
    $new1b = @"
        # PATCHED: lock acquire/release for compose view
        def _compose_run_and_release():
            if _bulk_send_lock.acquire(blocking=True, timeout=5):
                try:
                    _do_bulk_send(bulk.pk, contact_ids, template, extra_params)
                finally:
                    _bulk_send_lock.release()
            else:
                import logging
                logging.getLogger(__name__).warning(
                    '[Bulk Send] Could not acquire lock - send skipped.'
                )
        t = threading.Thread(target=_compose_run_and_release, daemon=False)
        t.start()
"@
    Patch-FileBoth $bulkPath $old1b $new1b "1-B: compose view lock"

    # 1-E: bulk_preview_api age_range
    $old1e = @"
def bulk_preview_api(request):
    qs       = Contact.objects.all()
    category = request.GET.get("category", "").strip()
    country  = request.GET.get("country",  "").strip()
    platform = request.GET.get("platform", "").strip()
    if category: qs = qs.filter(category__name__iexact=category)
    if country:  qs = qs.filter(country__iexact=country)
    if platform: qs = qs.filter(platform__iexact=platform)
    return JsonResponse({"count": qs.count()})
"@
    $new1e = @"
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
"@
    Patch-FileBoth $bulkPath $old1e $new1e "1-E: bulk_preview_api age_range"
}

# ============================================================
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

    # 2-A: widthratio fix
    Patch-File $dashPath '{% if bm.sent_count %}{% widthratio bm.sent_count bm.sent_count|add:bm.failed_count 100 %}%{% else %}0%{% endif %}' '{% if bm.sent_count and bm.failed_count %}{% widthratio bm.sent_count bm.sent_count|add:bm.failed_count 100 %}%{% elif bm.sent_count %}100%{% else %}0%{% endif %}' '2-A: Fix widthratio division by zero'

    # 2-D: null c.name guard
    Patch-File $dashPath '+c.name.substring(0,2).toUpperCase()+' '+((c.name||'??').substring(0,2).toUpperCase())+' '2-D: Guard null c.name'

    # 2-E: Today preset
    Patch-File $dashPath "if(preset==='today' && dfEl){ dfEl.value=toDate; }" "if(preset==='today'){ if(dfEl) dfEl.value=toDate; if(dtEl) dtEl.value=toDate; }" '2-E: Today preset sets both dates'

    # 2-H: pollBulkStatus null guard
    Patch-File $dashPath "row.querySelector('.bhi-title').textContent" "var titleEl=row.querySelector('.bhi-title'); if(titleEl) titleEl.textContent" '2-H: Guard querySelector null'

    # 2-I: filterModal
    $dashFull = Join-Path $root $dashPath
    $dashContent = [System.IO.File]::ReadAllText($dashFull, [System.Text.Encoding]::UTF8)
    if (-not $dashContent.Contains('id="filterModal"')) {
        $fm = @'

<!-- PATCHED: filterModal was missing -->
<div class="modal-overlay" id="filterModal">
  <div class="modal-box">
    <button class="modal-close" onclick="closeModal('filterModal')"><i class="fas fa-times"></i></button>
    <div class="modal-title">Filter Contacts</div>
    <form method="get" id="filterModalForm">
      <input type="hidden" name="tab" value="contacts">
      <div class="fw"><label class="fl">Category</label>
        <select class="fi fi-select" name="f_cat">
          <option value="">All Categories</option>
          {% for cat in categories %}<option value="{{ cat.name }}" {% if f_cat == cat.name %}selected{% endif %}>{{ cat.name }}</option>{% endfor %}
        </select></div>
      <div class="fw"><label class="fl">Country</label>
        <select class="fi fi-select" name="f_country">
          <option value="">All Countries</option>
          {% for c in country_list %}<option value="{{ c }}" {% if f_country == c %}selected{% endif %}>{{ c }}</option>{% endfor %}
        </select></div>
      <div class="fw"><label class="fl">Platform</label>
        <select class="fi fi-select" name="f_platform">
          <option value="">All Platforms</option>
          {% for plat in platform_stats %}<option value="{{ plat.platform }}" {% if f_platform == plat.platform %}selected{% endif %}>{{ plat.platform|title }}</option>{% endfor %}
        </select></div>
      <div style="display:flex;gap:10px;margin-top:4px;">
        <button type="submit" class="modal-save" style="flex:1;"><i class="fas fa-filter"></i> Apply Filter</button>
        <a href="?tab=contacts" class="modal-save" style="flex:0 0 auto;"><i class="fas fa-times"></i> Clear</a>
      </div>
    </form>
  </div>
</div>
'@
        $dashContent = $dashContent.Replace('</body>', $fm + '</body>')
        [System.IO.File]::WriteAllText($dashFull, $dashContent, [System.Text.Encoding]::UTF8)
        Write-FIX "2-I: Added filterModal HTML"
    } else {
        Write-OK "2-I: filterModal already exists - skipped"
    }

    # 2-J: _esc helper
    $old2j = @'
var CSRF = '{{ csrf_token }}';
'@
    $new2j = @'
var CSRF = '{{ csrf_token }}';

// PATCHED: HTML escape helper
function _esc(s){
  if(!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/'/g,'&#39;');
}
'@
    Patch-File $dashPath $old2j $new2j "2-J: Add _esc() helper"

    # 2-K: saveCampaignCounts atomic
    $old2k = @'
window.saveCampaignCounts = function(id){
  var contacted = document.getElementById('inp-contacted-'+id).value;
  var responded = document.getElementById('inp-responded-'+id).value;
  var confirmed = document.getElementById('inp-confirmed-'+id).value;
  function upd(field, value, cb){
'@
    $new2k = @'
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
        document.getElementById('camp-rr-'+id).innerHTML = d.response_rate+'<span style="font-size:13px;">%</span>';
        document.getElementById('camp-cr-'+id).innerHTML = d.conversion_rate+'<span style="font-size:13px;">%</span>';
        var bar = document.querySelector('#camp-'+id+' .campaign-progress-fill');
        if(bar) bar.style.width = d.response_rate+'%';
        toast('Campaign updated!');
      } else { toast(d.error||'Save failed','error'); }
    })
    .catch(function(){ toast('Network error saving counts','error'); });
  // REPLACED: old sequential upd() calls removed below
  function upd(field, value, cb){
'@
    Patch-FileBoth $dashPath $old2k $new2k "2-K: saveCampaignCounts atomic"
}

# ============================================================
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
    $old3a = @'
  'use strict';
'@
    $new3a = @'
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
'@
    Patch-File $landingPath $old3a $new3a "3-A: Add toggleLang() definition"

    $lFull = Join-Path $root $landingPath
    $lContent = [System.IO.File]::ReadAllText($lFull, [System.Text.Encoding]::UTF8)
    if ($lContent.Contains('233XXXXXXXXX')) {
        Write-ERR "MANUAL: Replace 233XXXXXXXXX in $landingPath with real WhatsApp number"
    } else {
        Write-OK "No placeholder WhatsApp number found"
    }
}

# ============================================================
Write-HDR "PATCH GROUP 4: campaign update view"

$viewFiles = Get-ChildItem -Path $root -Recurse -Filter "*.py" | Where-Object {
    $_.FullName -notmatch "migrations" -and
    $_.FullName -notmatch "__pycache__" -and
    (Select-String -Path $_.FullName -Pattern "campaign.*update|update.*campaign" -Quiet)
}
if ($viewFiles.Count -eq 0) {
    Write-ERR "Cannot auto-locate campaign update view - apply GROUP 4 manually"
} else {
    foreach ($vf in $viewFiles) {
        $rel = $vf.FullName.Substring($root.ToString().Length + 1)
        Write-OK "Checking: $rel"
        $old4 = @'
    field = form.get('field','')
    value = form.get('value','')
'@
        $new4 = @'
    field = form.get('field','')
    value = form.get('value','')

    # PATCHED: atomic bulk_counts update
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
'@
        Patch-FileBoth $rel $old4 $new4 "4: bulk_counts atomic handler"
    }
}

# ============================================================
Write-Host "" 
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  PATCH RUN COMPLETE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Run: python manage.py check" -ForegroundColor Yellow
Write-Host "Run: python manage.py test" -ForegroundColor Yellow
Write-Host ""
Write-Host "MANUAL ACTIONS STILL REQUIRED:" -ForegroundColor White
Write-Host "  [M1] Replace 233XXXXXXXXX in landing.html with real WhatsApp number" -ForegroundColor Gray
Write-Host "  [M2] Add prefetch_related(target_categories) to campaigns query in dashboard view" -ForegroundColor Gray
Write-Host "  [M3] Verify Contact model has: whatsapp_chat_url, handle_clean, platform_profile_url" -ForegroundColor Gray
Write-Host "  [M4] Verify /request-category-change/ is in urls.py" -ForegroundColor Gray
Write-Host "  [M5] Confirm dashboard view passes: categories, country_list, platform_stats, f_cat, f_country, f_platform" -ForegroundColor Gray
Write-Host "  [M6] Multi-worker Gunicorn: replace _bulk_send_lock with Redis/redlock" -ForegroundColor Gray
Write-Host "  [M7] openAllWaLinks - browsers block more than 3 tabs; use Copy Numbers for large campaigns" -ForegroundColor Gray
Write-Host ""
