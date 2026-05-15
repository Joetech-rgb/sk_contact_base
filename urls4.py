# contacts/urls.py
from django.urls import path
from . import views

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
    path("request-contacts/",        views.service_request_view,        name="service-request"),
    path("request-contacts/thanks/", views.service_request_thanks_view, name="service-request-thanks"),
    path("privacy/",        views.privacy_view,     name="privacy"),
    path("about/",          views.about_view,       name="about"),
    path("rules/",          views.rules_view,       name="rules"),
    path("delete-my-data/", views.delete_data_view, name="delete-my-data"),
]

