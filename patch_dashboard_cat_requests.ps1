# ============================================================
# patch_dashboard_cat_requests.ps1
# ============================================================
$ErrorActionPreference = "Stop"
$file = "templates\contacts\sk_dashboard.html"

$content = Get-Content $file -Raw -Encoding UTF8

# ── 1. Add wa_templates to the dashboard context ───────────
# Insert the category requests section before the closing of panel-categories
# Find the "Add New Category" button which is the last element in the categories panel

$oldCatEnd = '<button class="add-cat-btn" onclick="openModal(''addCatModal'')"><i class="fas fa-plus-circle"></i> Add New Category</button>


    </div>'

$newCatEnd = '<button class="add-cat-btn" onclick="openModal(''addCatModal'')"><i class="fas fa-plus-circle"></i> Add New Category</button>

      <div class="sh" style="margin-top:28px;">
        <div class="sh-title">Category Change Requests</div>
        <div class="sh-tag"><i class="fas fa-exchange-alt"></i> From registered users</div>
        <div class="sh-line"></div>
        <a href="/admin/contacts/categorychangerequest/" target="_blank" class="sh-action sh-action-ghost"><i class="fas fa-external-link-alt"></i> Open in Django Admin</a>
      </div>

      <div id="catRequestsList">
        {% for req in category_change_requests %}
        <div class="bulk-history-item" id="catreq-{{ req.pk }}" style="align-items:flex-start;">
          <div class="bhi-ico {% if req.status == ''pending'' %}sending{% elif req.status == ''done'' %}sent{% else %}failed{% endif %}">
            <i class="fas fa-{% if req.status == ''pending'' %}clock{% elif req.status == ''done'' %}check{% else %}times{% endif %}"></i>
          </div>
          <div class="bhi-info" style="flex:1;">
            <div class="bhi-title">
              <a href="https://wa.me/{{ req.whatsapp_number|cut:''+''}}" target="_blank" style="color:var(--blue-500);text-decoration:none;">{{ req.whatsapp_number }}</a>
              {% if req.full_name %}<span style="color:var(--gray-500);font-weight:400;"> &mdash; {{ req.full_name }}</span>{% endif %}
            </div>
            <div class="bhi-meta">
              {% if req.current_category %}<span style="background:var(--gray-100);padding:1px 7px;border-radius:100px;font-size:10px;">{{ req.current_category }}</span> &rarr; {% endif %}
              <span style="background:var(--blue-50);color:var(--blue-500);padding:1px 7px;border-radius:100px;font-size:10px;font-weight:700;">{{ req.requested_category }}</span>
              {% if req.reason %}<span style="color:var(--gray-400);"> &mdash; &ldquo;{{ req.reason|truncatechars:60 }}&rdquo;</span>{% endif %}
            </div>
            <div class="bhi-meta" style="margin-top:4px;">{{ req.submitted_at|date:"d M Y H:i" }}</div>
          </div>
          <div style="display:flex;gap:6px;flex-shrink:0;margin-top:2px;">
            {% if req.status == ''pending'' %}
            <button onclick="applyCatRequest({{ req.pk }}, this)" style="display:inline-flex;align-items:center;gap:5px;padding:5px 10px;border-radius:6px;font-size:11px;font-weight:600;background:var(--green-50);color:var(--green-700);border:1px solid #BBF7D0;cursor:pointer;font-family:inherit;transition:all 0.2s;">
              <i class="fas fa-check"></i> Apply
            </button>
            <button onclick="rejectCatRequest({{ req.pk }}, this)" style="display:inline-flex;align-items:center;gap:5px;padding:5px 10px;border-radius:6px;font-size:11px;font-weight:600;background:var(--red-50);color:var(--red-700);border:1px solid #FECACA;cursor:pointer;font-family:inherit;transition:all 0.2s;">
              <i class="fas fa-times"></i> Reject
            </button>
            {% else %}
            <span style="font-size:11px;font-weight:700;padding:4px 10px;border-radius:100px;{% if req.status == ''done'' %}background:var(--green-50);color:var(--green-700);{% else %}background:var(--red-50);color:var(--red-700);{% endif %}">
              {{ req.get_status_display }}
            </span>
            {% endif %}
          </div>
        </div>
        {% empty %}
        <div style="padding:20px;text-align:center;color:var(--gray-400);background:var(--white);border:1px solid var(--blue-100);border-radius:10px;">No category change requests yet.</div>
        {% endfor %}
      </div>

    </div>'

$content = $content.Replace($oldCatEnd, $newCatEnd)

# ── 2. Add JS functions for apply/reject before })(); ──────
$oldJsEnd = '// -- Init --------------------------------------------------'

$newJsEnd = '// -- Category Change Requests ----------------------------
window.applyCatRequest = function(id, btn) {
  if(!confirm(''Apply this category change to the contact?'')) return;
  var row = document.getElementById(''catreq-''+id);
  fetch(''/dashboard/catrequest/''+id+''/apply/'', {method:''POST'', headers:{''X-CSRFToken'':CSRF}})
    .then(function(r){ return r.json(); })
    .then(function(d){
      if(d.ok){
        toast(''Category updated!'');
        if(row){
          var actions = row.querySelector(''div[style*="flex-shrink"]:last-child'');
          if(actions) actions.innerHTML = ''<span style="font-size:11px;font-weight:700;padding:4px 10px;border-radius:100px;background:var(--green-50);color:var(--green-700);">Done</span>'';
          var ico = row.querySelector(''.bhi-ico'');
          if(ico){ ico.className=''bhi-ico sent''; ico.innerHTML=''<i class="fas fa-check"></i>''; }
        }
      } else { toast(d.error||''Failed'',''error''); }
    })
    .catch(function(){ toast(''Network error'',''error''); });
};

window.rejectCatRequest = function(id, btn) {
  if(!confirm(''Reject this request?'')) return;
  var row = document.getElementById(''catreq-''+id);
  fetch(''/dashboard/catrequest/''+id+''/reject/'', {method:''POST'', headers:{''X-CSRFToken'':CSRF}})
    .then(function(r){ return r.json(); })
    .then(function(d){
      if(d.ok){
        toast(''Request rejected.'');
        if(row){
          var actions = row.querySelector(''div[style*="flex-shrink"]:last-child'');
          if(actions) actions.innerHTML = ''<span style="font-size:11px;font-weight:700;padding:4px 10px;border-radius:100px;background:var(--red-50);color:var(--red-700);">Rejected</span>'';
          var ico = row.querySelector(''.bhi-ico'');
          if(ico){ ico.className=''bhi-ico failed''; ico.innerHTML=''<i class="fas fa-times"></i>''; }
        }
      } else { toast(d.error||''Failed'',''error''); }
    })
    .catch(function(){ toast(''Network error'',''error''); });
};

// -- Init --------------------------------------------------'

$content = $content.Replace($oldJsEnd, $newJsEnd)

Set-Content $file $content -Encoding UTF8
Write-Host "Dashboard patched." -ForegroundColor Green
Write-Host "Now patching dashboard.py to add context + views for apply/reject..." -ForegroundColor Cyan

# ── 3. Add category_change_requests to dashboard context ───
$dashPy = "contacts\views\dashboard.py"
$dashContent = Get-Content $dashPy -Raw -Encoding UTF8

# Add import
if ($dashContent -notmatch "CategoryChangeRequest") {
    $dashContent = $dashContent -replace "from contacts.models import \(", "from contacts.models import (
    CategoryChangeRequest,"
}

# Add to context query (after campaigns line)
$oldCommunityPosts = '    community_posts = CommunityPost.objects.all()'
$newCommunityPosts = '    community_posts = CommunityPost.objects.all()
    category_change_requests = CategoryChangeRequest.objects.select_related("requested_category").order_by("-submitted_at")[:50]'
$dashContent = $dashContent.Replace($oldCommunityPosts, $newCommunityPosts)

# Add to render context
$oldRenderEnd = '        # Google
        "google_connected":          google_connected,
        "google_account_email":      google_account_email,'
$newRenderEnd = '        # Google
        "google_connected":          google_connected,
        "google_account_email":      google_account_email,
        # Category change requests
        "category_change_requests":  category_change_requests,'
$dashContent = $dashContent.Replace($oldRenderEnd, $newRenderEnd)

# ── 4. Add apply/reject views at end of dashboard.py ───────
$applyRejectViews = @'


# ────────────────────────────────────────────────────────────
#  CATEGORY CHANGE REQUEST APPLY / REJECT
# ────────────────────────────────────────────────────────────

@login_required
@admin_required
@require_POST
def catrequest_apply_view(request, pk):
    from contacts.models import CategoryChangeRequest, Contact
    from django.utils import timezone as _tz
    req = get_object_or_404(CategoryChangeRequest, pk=pk)
    if req.status != 'pending':
        return JsonResponse({"ok": False, "error": "Request is not pending."})
    try:
        contact = Contact.objects.get(whatsapp_number=req.whatsapp_number)
        contact.category = req.requested_category
        contact.save(update_fields=["category"])
    except Contact.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Contact not found with that WhatsApp number."})
    req.status = "done"
    req.resolved_at = _tz.now()
    req.save(update_fields=["status", "resolved_at"])
    return JsonResponse({"ok": True})


@login_required
@admin_required
@require_POST
def catrequest_reject_view(request, pk):
    from contacts.models import CategoryChangeRequest
    from django.utils import timezone as _tz
    req = get_object_or_404(CategoryChangeRequest, pk=pk)
    req.status = "rejected"
    req.resolved_at = _tz.now()
    req.save(update_fields=["status", "resolved_at"])
    return JsonResponse({"ok": True})
'@

$dashContent = $dashContent.TrimEnd() + $applyRejectViews
Set-Content $dashPy $dashContent -Encoding UTF8
Write-Host "  dashboard.py patched." -ForegroundColor Green

# ── 5. Add to __init__.py ───────────────────────────────────
$initPy = "contacts\views\__init__.py"
$initContent = Get-Content $initPy -Raw -Encoding UTF8
if ($initContent -notmatch "catrequest_apply_view") {
    $initContent = $initContent -replace "from .dashboard import \(", "from .dashboard import (
    catrequest_apply_view, catrequest_reject_view,"
    Set-Content $initPy $initContent -Encoding UTF8
    Write-Host "  __init__.py patched." -ForegroundColor Green
}

# ── 6. Add URLs ─────────────────────────────────────────────
$urlsPy = "contacts\urls.py"
$urlsContent = Get-Content $urlsPy -Raw -Encoding UTF8
if ($urlsContent -notmatch "catrequest-apply") {
    $urlsContent = $urlsContent -replace "    # Category change request \(public AJAX\)", "    # Category change request actions (dashboard)
    path(`"dashboard/catrequest/<int:pk>/apply/`", views.catrequest_apply_view, name=`"catrequest-apply`"),
    path(`"dashboard/catrequest/<int:pk>/reject/`", views.catrequest_reject_view, name=`"catrequest-reject`"),

    # Category change request (public AJAX)"
    Set-Content $urlsPy $urlsContent -Encoding UTF8
    Write-Host "  urls.py patched." -ForegroundColor Green
}

Write-Host ""
Write-Host "All done! Restart server: python manage.py runserver" -ForegroundColor Yellow
Write-Host "Category change requests now appear in dashboard > Categories tab"
