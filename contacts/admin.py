from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from django.db.models import Count, Q
from django.urls import path
from django.shortcuts import render
import csv
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime
from .models import Contact, ContactStats, AutomationLog
from django.utils.safestring import mark_safe



@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """
    Enhanced Admin interface for Contact management
    """
    
    # List Display
    list_display = [
        'formatted_name',
        'category_badge',
        'country',
        'social_media_badge',
        'followers_display',
        'age_category',
        'whatsapp_link',
        'days_since_added',
        'sync_status',
    ]
    
    # Filters
    list_filter = [
        'category',
        'age_category',
        'country',
        'social_media_platform',
        'whatsapp_message_sent',
        'synced_to_drive',
        'date_added',
    ]
    
    # Search
    search_fields = [
        'first_name',
        'surname',
        'email',
        'whatsapp_contact',
        'social_media_handle',
        'country',
    ]
    
    # Ordering
    ordering = ['-followers_count', '-date_added']
    
    # Fields Layout
    fieldsets = (
        ('Basic Information', {
            'fields': ('first_name', 'surname', 'email', 'whatsapp_contact')
        }),
        ('Categorization', {
            'fields': ('category', 'age_category', 'country', 'country_code')
        }),
        ('Social Media', {
            'fields': ('social_media_platform', 'social_media_handle', 'followers_count')
        }),
        ('Additional Information', {
            'fields': ('school', 'level', 'notes'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('whatsapp_message_sent', 'whatsapp_message_date', 'synced_to_drive'),
            'classes': ('collapse',)
        }),
    )
    
    # Read-only fields
    readonly_fields = ['date_added', 'last_updated']
    
    # Actions
    actions = [
        'export_to_excel',
        'export_to_csv',
        'mark_as_messaged',
        'mark_as_synced',
        'send_whatsapp_batch',
    ]
    
    # Custom columns
    def formatted_name(self, obj):
        """Display formatted name with icon"""
        return format_html(
            '<strong>👤 {} {}</strong>',
            obj.first_name,
            obj.surname
        )
    formatted_name.short_description = 'Name'
    
    def category_badge(self, obj):
        """Display category as colored badge"""
        colors = {
            'face_card': '#FF6B6B',
            'chubby': '#4ECDC4',
            'brand_owner': '#45B7D1',
            'slim': '#96CEB4',
            'curvy': '#FFEAA7',
            'dark_skin': '#6C5CE7',
            'half_cast': '#FD79A8',
        }
        color = colors.get(obj.category, '#95A5A6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_category_display()
        )
    category_badge.short_description = 'Category'
    
    def social_media_badge(self, obj):
        """Display social media platform with icon"""
        icons = {
            'linkedin': '💼',
            'instagram': '📸',
            'facebook': '👥',
            'snapchat': '👻',
            'tiktok': '🎵',
            'twitter': '🐦',
            'youtube': '▶️',
        }
        icon = icons.get(obj.social_media_platform, '🌐')
        return format_html(
            '{} {}',
            icon,
            obj.get_social_media_platform_display()
        )
    social_media_badge.short_description = 'Platform'
    
    def followers_display(self, obj):
        """Display followers count with formatting"""
        if obj.followers_count >= 1000000:
            return format_html('<strong style="color: #e74c3c;">{}M</strong>', round(obj.followers_count / 1000000, 1))
        elif obj.followers_count >= 1000:
            return format_html('<strong style="color: #f39c12;">{}K</strong>', round(obj.followers_count / 1000, 1))
        else:
            return format_html('<span>{}</span>', obj.followers_count)
    followers_display.short_description = 'Followers'
    followers_display.admin_order_field = 'followers_count'
    
    def whatsapp_link(self, obj):
        """Display clickable WhatsApp link"""
        return format_html(
            '<a href="{}" target="_blank" style="color: #25D366; text-decoration: none;">💬 Message</a>',
            obj.get_whatsapp_link()
        )
    whatsapp_link.short_description = 'WhatsApp'
    
    def sync_status(self, obj):
        """Display sync status"""
        if obj.synced_to_drive:
            return mark_safe('<span style="color: #27ae60;">✓ Synced</span>')
        return mark_safe('<span style="color: #95a5a6;">○ Not Synced</span>')
    sync_status.short_description = 'Drive Status'
    
    # Export Actions
    def export_to_excel(self, request, queryset):
        """Export selected contacts to Excel with formatting"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "SK Contacts"
        
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        headers = [
            'First Name', 'Surname', 'Full Name', 'WhatsApp Contact', 'Email',
            'Category', 'Age Category', 'Country', 'Country Code',
            'Social Media', 'Handle', 'Followers', 'School', 'Level',
            'Date Added', 'Days Since Added', 'WhatsApp Sent', 'Drive Synced'
        ]
        
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        for row, contact in enumerate(queryset, start=2):
            ws.cell(row=row, column=1, value=contact.first_name)
            ws.cell(row=row, column=2, value=contact.surname)
            ws.cell(row=row, column=3, value=contact.full_name)
            ws.cell(row=row, column=4, value=contact.whatsapp_contact)
            ws.cell(row=row, column=5, value=contact.email or '')
            ws.cell(row=row, column=6, value=contact.get_category_display())
            ws.cell(row=row, column=7, value=contact.age_category)
            ws.cell(row=row, column=8, value=contact.country)
            ws.cell(row=row, column=9, value=contact.country_code)
            ws.cell(row=row, column=10, value=contact.get_social_media_platform_display())
            ws.cell(row=row, column=11, value=contact.social_media_handle or '')
            ws.cell(row=row, column=12, value=contact.followers_count)
            ws.cell(row=row, column=13, value=contact.school or '')
            ws.cell(row=row, column=14, value=contact.level or '')
            ws.cell(row=row, column=15, value=contact.date_added.strftime('%Y-%m-%d %H:%M'))
            ws.cell(row=row, column=16, value=contact.days_since_added)
            ws.cell(row=row, column=17, value='Yes' if contact.whatsapp_message_sent else 'No')
            ws.cell(row=row, column=18, value='Yes' if contact.synced_to_drive else 'No')
        
        for column in ws.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column[0].column_letter].width = adjusted_width
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f'SK_Contacts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        wb.save(response)
        
        self.message_user(request, f"{queryset.count()} contacts exported to Excel successfully!")
        return response
    
    export_to_excel.short_description = "📊 Export to Excel (.xlsx)"
    
    def export_to_csv(self, request, queryset):
        """Export selected contacts to CSV"""
        response = HttpResponse(content_type='text/csv')
        filename = f'SK_Contacts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow([
            'First Name', 'Surname', 'Full Name', 'WhatsApp Contact', 'Email',
            'Category', 'Age Category', 'Country', 'Country Code',
            'Social Media', 'Handle', 'Followers', 'School', 'Level',
            'Date Added', 'Days Since Added', 'WhatsApp Sent', 'Drive Synced'
        ])
        
        for contact in queryset:
            writer.writerow([
                contact.first_name,
                contact.surname,
                contact.full_name,
                contact.whatsapp_contact,
                contact.email or '',
                contact.get_category_display(),
                contact.age_category,
                contact.country,
                contact.country_code,
                contact.get_social_media_platform_display(),
                contact.social_media_handle or '',
                contact.followers_count,
                contact.school or '',
                contact.level or '',
                contact.date_added.strftime('%Y-%m-%d %H:%M'),
                contact.days_since_added,
                'Yes' if contact.whatsapp_message_sent else 'No',
                'Yes' if contact.synced_to_drive else 'No',
            ])
        
        self.message_user(request, f"{queryset.count()} contacts exported to CSV successfully!")
        return response
    
    export_to_csv.short_description = "📄 Export to CSV"
    
    def mark_as_messaged(self, request, queryset):
        """Mark selected contacts as messaged"""
        from django.utils import timezone
        updated = queryset.update(
            whatsapp_message_sent=True,
            whatsapp_message_date=timezone.now()
        )
        self.message_user(request, f"{updated} contacts marked as messaged.")
    
    mark_as_messaged.short_description = "✅ Mark as WhatsApp Messaged"
    
    def mark_as_synced(self, request, queryset):
        """Mark selected contacts as synced to Drive"""
        updated = queryset.update(synced_to_drive=True)
        self.message_user(request, f"{updated} contacts marked as synced to Google Drive.")
    
    mark_as_synced.short_description = "☁️ Mark as Synced to Drive"
    
    def send_whatsapp_batch(self, request, queryset):
        """Placeholder for WhatsApp batch sending"""
        self.message_user(
            request,
            f"WhatsApp batch sending feature - {queryset.count()} contacts selected. "
            "Please configure WhatsApp Business API integration.",
            level='warning'
        )
    
    send_whatsapp_batch.short_description = "💬 Send WhatsApp Batch (requires API setup)"


@admin.register(ContactStats)
class ContactStatsAdmin(admin.ModelAdmin):
    """Admin interface for Contact Statistics"""
    list_display = ['date', 'total_contacts', 'contacts_added_today']
    list_filter = ['date']
    ordering = ['-date']


@admin.register(AutomationLog)
class AutomationLogAdmin(admin.ModelAdmin):
    """Admin interface for Automation Logs"""
    list_display = ['contact', 'action_type', 'status', 'timestamp']
    list_filter = ['action_type', 'status', 'timestamp']
    search_fields = ['contact__first_name', 'contact__surname', 'details']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']