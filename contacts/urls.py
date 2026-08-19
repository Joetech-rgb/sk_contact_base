# contacts/urls.py
from django.urls import path
from . import views
from contacts.views.whatsapp_webhook import whatsapp_webhook

urlpatterns = [
    path("",             views.landing_view,   name="landing"),
    path("thank-you/",   views.thank_you_view, name="thank-you"),
    path("login/",  views.admin_login_view,  name="login"),
    path("logout/", views.admin_logout_view, name="logout"),
    path("dashboard/",    views.sk_dashboard_view, name="dashboard"),
    path("sk-dashboard/", views.sk_dashboard_view, name="sk-dashboard"),
    path("contacts/",                 views.contact_list_view,   name="contact-list"),
    path("contacts/add/",             views.contact_add_view,    name="contact-add"),
    path("contacts/<int:pk>/edit/",   views.contact_edit_view,   name="contact-edit"),
    path("contacts/<int:pk>/delete/", views.contact_delete_view, name="contact-delete"),
    path("api/contacts/<int:pk>/",    views.contact_detail_api,  name="contact-detail-api"),
    path("contacts/category/add/",             views.category_add_view,    name="category-add"),
    path("contacts/category/<int:pk>/toggle/", views.category_toggle_view, name="category-toggle"),
    path("contacts/category/<int:pk>/delete/", views.category_delete_view, name="category-delete"),
    path("export/csv/", views.export_csv_view, name="export-csv"),
    path("export/vcf/", views.export_vcf_view, name="export-vcf"),
    path("dashboard/google/oauth/",      views.google_oauth_start,    name="google-oauth-start"),
    path("dashboard/google/callback/",   views.google_oauth_callback, name="google-oauth-callback"),
    path("dashboard/google/disconnect/", views.google_disconnect,     name="google-disconnect"),
    path("dashboard/google/sync/",       views.google_sync,           name="google-sync"),
    path("dashboard/bulk/",         views.bulk_compose_view, name="bulk-compose"),
    path("dashboard/bulk/history/", views.bulk_history_view, name="bulk-history"),
    path("api/bulk/preview/",       views.bulk_preview_api,  name="bulk-preview-api"),
    path("api/bulk/send/",          views.bulk_send_api,     name="bulk-send-api"),
    path("api/bulk/status/<int:bulk_id>/", views.bulk_status_api, name="bulk-status-api"),
    path("request-contacts/",        views.service_request_view,        name="service-request"),
    path("request-contacts/thanks/", views.service_request_thanks_view, name="service-request-thanks"),
    path("privacy/",        views.privacy_view,     name="privacy"),
    path("about/",          views.about_view,       name="about"),
    path("rules/",          views.rules_view,       name="rules"),
    path("delete-my-data/", views.delete_data_view, name="delete-my-data"),

    # Campaign URLs
    path("dashboard/campaign/create/",              views.campaign_create_view,  name="campaign-create"),
    path("dashboard/campaign/<int:pk>/update/",     views.campaign_update_view,  name="campaign-update"),
    path("api/campaign/<int:pk>/increment-contacted/", views.campaign_increment_contacted, name="campaign-increment-contacted"),
    path("api/campaign/<int:camp_pk>/contact/<int:contact_pk>/status/", views.campaign_contact_status_api, name="campaign-contact-status"),
    path("api/campaign/<int:pk>/contacts/", views.campaign_contacts_api, name="campaign-contacts-api"),
    path("dashboard/campaign/<int:pk>/delete/",     views.campaign_delete_view,  name="campaign-delete"),

    # Post / Updates URLs
    path("dashboard/post/create/",                  views.post_create_view,      name="post-create"),
    path("dashboard/post/<int:pk>/toggle/",         views.post_toggle_view,      name="post-toggle"),
    path("dashboard/post/<int:pk>/delete/",         views.post_delete_view,      name="post-delete"),

    # Account link URL
    path("dashboard/account-link/save/",            views.account_link_save_view, name="account-link-save"),

    # Template URL
    path("dashboard/template/save/",                views.template_save_view,     name="template-save"),

    # Category change request actions (dashboard)
    path("dashboard/catrequest/<int:pk>/apply/", views.catrequest_apply_view, name="catrequest-apply"),
    path("dashboard/catrequest/<int:pk>/reject/", views.catrequest_reject_view, name="catrequest-reject"),

    # Category change request (public AJAX)
    path("request-category-change/", views.category_change_request_view, name="category-change-request"),
    path("whatsapp/webhook/", whatsapp_webhook, name="whatsapp-webhook"),

    # Site settings (dashboard toggles)
    path("dashboard/settings/toggle-education/", views.settings_toggle_education_view, name="settings-toggle-education"),
]

# --- Added by fix_whatsapp_reply script ---
from contacts.views.dashboard import send_reply_view as _sk_send_reply_view
from contacts.views.dashboard import wa_latest_log_id_view as _sk_wa_latest_log_id_view

urlpatterns += [
    path("dashboard/reply/send/", _sk_send_reply_view, name="send-reply"),
    path('dashboard/wa-log/latest/', _sk_wa_latest_log_id_view, name='wa_latest_log_id'),
    path('dashboard/wa-log/thread/', __import__('contacts.views.dashboard', fromlist=['wa_thread_view']).wa_thread_view, name='wa-thread'),
]

# --- SEO: robots.txt + sitemap.xml ---
from django.http import HttpResponse

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /dashboard/",
        "Disallow: /login/",
        "Disallow: /api/",
        "Disallow: /export/",
        "Disallow: /request-category-change/",
        "Sitemap: https://skcommunitybase.com/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

def sitemap_xml(request):
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://skcommunitybase.com/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>
  <url><loc>https://skcommunitybase.com/about/</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
  <url><loc>https://skcommunitybase.com/privacy/</loc><changefreq>yearly</changefreq><priority>0.3</priority></url>
  <url><loc>https://skcommunitybase.com/rules/</loc><changefreq>yearly</changefreq><priority>0.3</priority></url>
</urlset>'''
    return HttpResponse(xml, content_type="application/xml")

urlpatterns += [
    path("robots.txt", robots_txt, name="robots-txt"),
    path("sitemap.xml", sitemap_xml, name="sitemap-xml"),
]
