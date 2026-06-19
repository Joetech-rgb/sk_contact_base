# ============================================================
# patch_admin.ps1
# Run from your Django project root:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\patch_admin.ps1
# ============================================================

$ErrorActionPreference = "Stop"

$adminPy = "contacts\admin.py"

Write-Host "Patching $adminPy ..." -ForegroundColor Cyan

$newBlock = @'


# ──────────────────────────────────────────────────────────────
# CATEGORY CHANGE REQUEST ADMIN
# ──────────────────────────────────────────────────────────────
from contacts.models import CategoryChangeRequest
from django.utils import timezone as _tz

@admin.register(CategoryChangeRequest)
class CategoryChangeRequestAdmin(admin.ModelAdmin):

    list_display = [
        'whatsapp_link',
        'full_name',
        'current_category',
        'requested_category',
        'reason_short',
        'status_badge',
        'submitted_at',
    ]

    list_filter  = ['status', 'requested_category']

    search_fields = ['whatsapp_number', 'full_name', 'current_category']

    ordering = ['-submitted_at']

    readonly_fields = ['whatsapp_number', 'full_name', 'current_category',
                       'requested_category', 'reason', 'submitted_at', 'resolved_at']

    actions = ['mark_done', 'mark_rejected', 'apply_category_change']

    fieldsets = (
        ('Request Details', {
            'fields': ('whatsapp_number', 'full_name', 'current_category',
                       'requested_category', 'reason'),
        }),
        ('Status', {
            'fields': ('status', 'submitted_at', 'resolved_at'),
        }),
    )

    # ── Custom columns ─────────────────────────────────────────

    def whatsapp_link(self, obj):
        clean = obj.whatsapp_number.replace('+', '').replace(' ', '')
        return format_html(
            '<a href="https://wa.me/{}" target="_blank" '
            'style="color:#25D366;font-weight:600;white-space:nowrap;">'
            '💬 {}</a>',
            clean, obj.whatsapp_number
        )
    whatsapp_link.short_description = 'WhatsApp'

    def reason_short(self, obj):
        if not obj.reason:
            return '—'
        return obj.reason[:60] + ('…' if len(obj.reason) > 60 else '')
    reason_short.short_description = 'Reason'

    def status_badge(self, obj):
        colours = {
            'pending':  ('#FEF3C7', '#B45309'),
            'done':     ('#DCFCE7', '#15803D'),
            'rejected': ('#FEE2E2', '#B91C1C'),
        }
        bg, fg = colours.get(obj.status, ('#F1F5F9', '#334155'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;border-radius:100px;'
            'font-size:11px;font-weight:700;">{}</span>',
            bg, fg, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    # ── Bulk actions ───────────────────────────────────────────

    @admin.action(description='✅ Mark selected as Done')
    def mark_done(self, request, queryset):
        updated = queryset.update(status='done', resolved_at=_tz.now())
        self.message_user(request, f'{updated} request(s) marked as Done.')

    @admin.action(description='❌ Mark selected as Rejected')
    def mark_rejected(self, request, queryset):
        updated = queryset.update(status='rejected', resolved_at=_tz.now())
        self.message_user(request, f'{updated} request(s) marked as Rejected.')

    @admin.action(description='🔄 Apply category change to Contact record')
    def apply_category_change(self, request, queryset):
        applied = 0
        skipped = 0
        for req in queryset.filter(status='pending'):
            try:
                contact = Contact.objects.get(whatsapp_number=req.whatsapp_number)
                contact.category = req.requested_category
                contact.save(update_fields=['category'])
                req.status      = 'done'
                req.resolved_at = _tz.now()
                req.save(update_fields=['status', 'resolved_at'])
                applied += 1
            except Contact.DoesNotExist:
                skipped += 1
        msg = f'{applied} category change(s) applied.'
        if skipped:
            msg += f' {skipped} skipped (contact not found by WhatsApp number).'
        self.message_user(request, msg)
'@

$content = Get-Content $adminPy -Raw
$content = $content.TrimEnd() + $newBlock
Set-Content $adminPy $content -Encoding UTF8

Write-Host "  admin.py patched." -ForegroundColor Green
Write-Host ""
Write-Host "All done! CategoryChangeRequest is now in your Django admin." -ForegroundColor Yellow
Write-Host "  - Go to /admin/contacts/categorychangerequest/ to see requests"
Write-Host "  - Use 'Apply category change' action to update the contact in one click"
Write-Host "  - Restart your server: python manage.py runserver"
