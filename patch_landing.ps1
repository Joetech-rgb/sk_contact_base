# ============================================================
# patch_landing.ps1
# Run from your Django project root:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\patch_landing.ps1
# ============================================================

$ErrorActionPreference = "Stop"

$landingHtml = "templates\contacts\landing.html"

Write-Host "Patching $landingHtml ..." -ForegroundColor Cyan

$content = Get-Content $landingHtml -Raw -Encoding UTF8

# ── 1. Add "Change My Category" button in the footer link row ──
# Insert it after the "Work With Us" button
$oldFooterBtn = 'onclick="openPolicy(''workModal'')" style="background:none;border:none;font-size:12px;color:rgba(255,255,255,0.45);cursor:pointer;font-family:''DM Sans'',sans-serif;">Work With Us</button>'

$newFooterBtn = 'onclick="openPolicy(''workModal'')" style="background:none;border:none;font-size:12px;color:rgba(255,255,255,0.45);cursor:pointer;font-family:''DM Sans'',sans-serif;">Work With Us</button>
    <button type="button" onclick="openPolicy(''catChangeModal'')" style="background:none;border:none;font-size:12px;color:rgba(255,255,255,0.45);cursor:pointer;font-family:''DM Sans'',sans-serif;">Change My Category</button>'

$content = $content.Replace($oldFooterBtn, $newFooterBtn)

# ── 2. Insert the category change modal just before the closing </footer> ──
$catChangeModal = @'

<!-- ══ CATEGORY CHANGE REQUEST MODAL ═══════════════════════════ -->
<div class="modal-overlay" id="catChangeModal">
  <div class="modal-box">
    <button class="modal-close" onclick="closePolicy('catChangeModal')" type="button"><i class="fas fa-times"></i></button>
    <div class="modal-title">Change My Category</div>
    <p class="modal-sub">Already registered? Ask the admin to update your category.</p>

    <div class="fw" style="margin-bottom:12px;">
      <label class="fl">Your WhatsApp Number <span style="color:var(--blue-300);">*</span></label>
      <input type="text" id="ccWhatsapp" placeholder="+233241234567">
    </div>

    <div class="fw" style="margin-bottom:12px;">
      <label class="fl">Your Name</label>
      <input type="text" id="ccName" placeholder="Helps the admin find you faster">
    </div>

    <div class="fw" style="margin-bottom:12px;">
      <label class="fl">New Category <span style="color:var(--blue-300);">*</span></label>
      <select id="ccCategory">
        <option value="">-- Select a category --</option>
        {% for cat in active_categories %}
        <option value="{{ cat.pk }}">{{ cat.name }}</option>
        {% endfor %}
      </select>
    </div>

    <div class="fw" style="margin-bottom:4px;">
      <label class="fl">Reason (optional)</label>
      <textarea id="ccReason" rows="3" placeholder="Why do you want to change your category?" style="resize:vertical;"></textarea>
    </div>

    <div id="ccMsg" style="display:none;margin-top:10px;padding:10px 14px;border-radius:8px;font-size:13px;font-weight:600;"></div>

    <button class="modal-save" onclick="submitCatChange()" type="button" id="ccSubmitBtn">
      <i class="fas fa-paper-plane"></i> Submit Request
    </button>
  </div>
</div>

'@

$content = $content.Replace('</footer>', $catChangeModal + '</footer>')

# ── 3. Add catChangeModal to the Escape key handler ──
$oldEscape = "['rulesModal','privacyModal','workModal','aboutModal','optModal'].forEach(function(id) {"
$newEscape = "['rulesModal','privacyModal','workModal','aboutModal','optModal','catChangeModal'].forEach(function(id) {"
$content = $content.Replace($oldEscape, $newEscape)

# ── 4. Add the submitCatChange JS before the closing })(); of the main IIFE ──
$catChangeJs = @'

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
        msg.style.display = 'block';
        msg.style.cssText = 'display:block;margin-top:10px;padding:10px 14px;border-radius:8px;font-size:13px;font-weight:600;background:#FEE2E2;border:1px solid #FECACA;color:#B91C1C;';
        msg.innerHTML = '<i class="fas fa-exclamation-circle"></i> Please enter your WhatsApp number and select a category.';
      }
      return;
    }

    if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...'; }
    if (msg) { msg.style.display = 'none'; }

    var form = new FormData();
    form.append('whatsapp_number',    wa);
    form.append('full_name',          nm);
    form.append('requested_category', cat);
    form.append('reason',             rsn);

    // Get CSRF token from the main registration form
    var csrf = '';
    var csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) csrf = csrfInput.value;

    fetch('/request-category-change/', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf },
      body: form
    })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (msg) {
        msg.style.display = 'block';
        if (d.ok) {
          msg.style.cssText = 'display:block;margin-top:10px;padding:10px 14px;border-radius:8px;font-size:13px;font-weight:600;background:#DCFCE7;border:1px solid #BBF7D0;color:#15803D;';
          msg.innerHTML = '<i class="fas fa-check-circle"></i> ' + d.message;
          // Clear the form on success
          ['ccWhatsapp','ccName','ccReason'].forEach(function(id) {
            var el = document.getElementById(id); if (el) el.value = '';
          });
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
        msg.style.display = 'block';
        msg.style.cssText = 'display:block;margin-top:10px;padding:10px 14px;border-radius:8px;font-size:13px;font-weight:600;background:#FEE2E2;border:1px solid #FECACA;color:#B91C1C;';
        msg.innerHTML = '<i class="fas fa-exclamation-circle"></i> Network error. Please try again.';
      }
      if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Request'; }
    });
  };

'@

# Insert just before the closing })(); of the main script block
$oldScriptEnd = "})();`n</script>"
$newScriptEnd = $catChangeJs + "})();`n</script>"
$content = $content.Replace($oldScriptEnd, $newScriptEnd)

# Also need active_categories in the landing view context — check first
if ($content -match "active_categories") {
    Write-Host "  active_categories already in template." -ForegroundColor Gray
} else {
    Write-Host "  WARNING: active_categories not found in template — make sure your landing view passes it." -ForegroundColor Yellow
}

Set-Content $landingHtml $content -Encoding UTF8
Write-Host "  landing.html patched." -ForegroundColor Green

# ── 5. Check if landing view passes active_categories ──────────
Write-Host ""
Write-Host "Checking views/public.py for active_categories context..." -ForegroundColor Cyan
$publicPy = "contacts\views\public.py"
$publicContent = Get-Content $publicPy -Raw

if ($publicContent -match "active_categories") {
    Write-Host "  active_categories already passed in landing view context." -ForegroundColor Green
} else {
    Write-Host "  active_categories NOT found in landing view — patching now..." -ForegroundColor Yellow

    # Add Category to imports if not already there (it was added in previous patch)
    # Patch the render call to add active_categories to context
    $oldRender = '"form":           form,
        "total_contacts": Contact.objects.count(),
        "ref_slug":       ref_slug,
        "notifications":  notifications,'

    $newRender = '"form":           form,
        "total_contacts": Contact.objects.count(),
        "ref_slug":       ref_slug,
        "notifications":  notifications,
        "active_categories": Category.objects.filter(is_active=True).order_by("name"),'

    $publicContent = $publicContent.Replace($oldRender, $newRender)
    Set-Content $publicPy $publicContent -Encoding UTF8
    Write-Host "  public.py context updated with active_categories." -ForegroundColor Green
}

Write-Host ""
Write-Host "All done!" -ForegroundColor Yellow
Write-Host "  - 'Change My Category' button added to the footer"
Write-Host "  - Category change modal added to landing.html"
Write-Host "  - AJAX submit JS wired to /request-category-change/"
Write-Host "  - Restart your server: python manage.py runserver"
