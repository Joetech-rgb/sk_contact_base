# ============================================================
# fix_contact_count.ps1
# Run from your Django project root:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\fix_contact_count.ps1
# ============================================================

$ErrorActionPreference = "Stop"

$dashboardPy = "contacts\views\dashboard.py"

Write-Host "Patching $dashboardPy ..." -ForegroundColor Cyan

$content = Get-Content $dashboardPy -Raw -Encoding UTF8

$oldLine = 'categories = Category.objects.annotate(
        contact_count=Count("contact")
    ).order_by("name")'

$newLine = 'categories = Category.objects.order_by("name")'

if ($content -match [regex]::Escape('contact_count=Count("contact")')) {
    $content = $content.Replace($oldLine, $newLine)
    Set-Content $dashboardPy $content -Encoding UTF8
    Write-Host "  Fixed. annotation removed — model property handles contact_count." -ForegroundColor Green
} else {
    Write-Host "  Pattern not found — checking for single-line version..." -ForegroundColor Yellow
    $oldLineSingle = 'categories = Category.objects.annotate(contact_count=Count("contact")).order_by("name")'
    if ($content -match [regex]::Escape($oldLineSingle)) {
        $content = $content.Replace($oldLineSingle, $newLine)
        Set-Content $dashboardPy $content -Encoding UTF8
        Write-Host "  Fixed (single-line version)." -ForegroundColor Green
    } else {
        Write-Host "  Could not find the annotation line automatically." -ForegroundColor Red
        Write-Host "  Manually replace this in dashboard.py:" -ForegroundColor Yellow
        Write-Host '    categories = Category.objects.annotate(contact_count=Count("contact")).order_by("name")'
        Write-Host "  With:"
        Write-Host '    categories = Category.objects.order_by("name")'
    }
}

Write-Host ""
Write-Host "Done. Restart your server: python manage.py runserver" -ForegroundColor Yellow
