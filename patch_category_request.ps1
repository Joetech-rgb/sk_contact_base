# ============================================================
# patch_category_request.ps1
# Run from your Django project root:
#   .\patch_category_request.ps1
# ============================================================

$ErrorActionPreference = "Stop"

# ── Paths — adjust if your app lives elsewhere ──────────────
$viewsDir = "contacts\views"
$publicPy = "$viewsDir\public.py"
$initPy   = "$viewsDir\__init__.py"
$urlsPy   = "contacts\urls.py"

# ── 1. Patch public.py ──────────────────────────────────────
Write-Host "Patching $publicPy ..." -ForegroundColor Cyan

$newImportLine = "from ..models import Contact, Notification, ReferralSource, CommunityPost, Category, CategoryChangeRequest"

$publicContent = Get-Content $publicPy -Raw

# Replace the existing models import line
$publicContent = $publicContent -replace `
    "from \.\.models import Contact, Notification, ReferralSource, CommunityPost", `
    $newImportLine

# Append the new view at the end of the file
$categoryChangeView = @'


def category_change_request_view(request):
    """
    AJAX endpoint — user submits a category change request from the landing page.
    Returns JSON so it works without a page reload.
    """
    from django.http import JsonResponse
    from django.views.decorators.http import require_POST

    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)

    whatsapp      = request.POST.get("whatsapp_number", "").strip()
    full_name     = request.POST.get("full_name", "").strip()
    requested_id  = request.POST.get("requested_category", "").strip()
    reason        = request.POST.get("reason", "").strip()

    if not whatsapp or not requested_id:
        return JsonResponse({"ok": False, "error": "WhatsApp number and category are required."})

    try:
        category = Category.objects.get(pk=requested_id, is_active=True)
    except Category.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Invalid category selected."})

    # Block duplicate pending requests for the same number + category
    already = CategoryChangeRequest.objects.filter(
        whatsapp_number=whatsapp,
        requested_category=category,
        status="pending",
    ).exists()
    if already:
        return JsonResponse({
            "ok": False,
            "error": "You already have a pending request for this category.",
        })

    # Pull current category from the contact record if it exists
    current = ""
    try:
        contact = Contact.objects.get(whatsapp_number=whatsapp)
        current = contact.category.name if contact.category else ""
    except Contact.DoesNotExist:
        pass

    CategoryChangeRequest.objects.create(
        whatsapp_number=whatsapp,
        full_name=full_name,
        current_category=current,
        requested_category=category,
        reason=reason,
    )

    return JsonResponse({
        "ok": True,
        "message": "Request submitted! The admin will update your category shortly.",
    })
'@

$publicContent = $publicContent.TrimEnd() + $categoryChangeView

Set-Content $publicPy $publicContent -Encoding UTF8
Write-Host "  public.py patched." -ForegroundColor Green


# ── 2. Patch __init__.py ────────────────────────────────────
Write-Host "Patching $initPy ..." -ForegroundColor Cyan

$initContent = Get-Content $initPy -Raw

# Add category_change_request_view to the public import line
$initContent = $initContent -replace `
    "from \.public\s+import landing_view, thank_you_view", `
    "from .public    import landing_view, thank_you_view, category_change_request_view"

Set-Content $initPy $initContent -Encoding UTF8
Write-Host "  __init__.py patched." -ForegroundColor Green


# ── 3. Patch urls.py ────────────────────────────────────────
Write-Host "Patching $urlsPy ..." -ForegroundColor Cyan

$urlsContent = Get-Content $urlsPy -Raw

# Add new URL before the closing bracket of urlpatterns
$newUrl = @'

    # Category change request (public AJAX)
    path("request-category-change/", views.category_change_request_view, name="category-change-request"),
]
'@

$urlsContent = $urlsContent -replace "\](\s*)$", $newUrl

Set-Content $urlsPy $urlsContent -Encoding UTF8
Write-Host "  urls.py patched." -ForegroundColor Green


# ── 4. Run migrations ───────────────────────────────────────
Write-Host "`nRunning migrations ..." -ForegroundColor Cyan
python manage.py makemigrations
python manage.py migrate
Write-Host "  Migrations done." -ForegroundColor Green


Write-Host "`nAll done! Next steps:" -ForegroundColor Yellow
Write-Host "  1. Add the modal HTML + JS to your landing.html (see instructions)"
Write-Host "  2. Register CategoryChangeRequest in contacts/admin.py so you can action requests"
Write-Host "  3. Restart your dev server: python manage.py runserver"
