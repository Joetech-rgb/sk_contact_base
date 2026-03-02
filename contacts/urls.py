from django.urls import path
from . import views

urlpatterns = [
    # Landing page - public sign-up form
    path('', views.landing_view, name='landing'),

    # Thank you page after sign-up
    path('thank-you/', views.thank_you_view, name='thank-you'),

    # Admin Login / Logout
    path('login/', views.admin_login_view, name='login'),
    path('logout/', views.admin_logout_view, name='logout'),

    # Dashboard - protected, redirects to login if not logged in
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Contact CRUD
    path('contacts/', views.ContactListView.as_view(), name='contact-list'),
    path('contacts/add/', views.ContactCreateView.as_view(), name='contact-add'),
    path('contacts/<int:pk>/edit/', views.ContactUpdateView.as_view(), name='contact-edit'),
    path('contacts/<int:pk>/delete/', views.ContactDeleteView.as_view(), name='contact-delete'),

    # Export
    path('export/excel/', views.export_contacts_excel, name='export-excel'),
    path('export/csv/', views.export_contacts_csv, name='export-csv'),

    # API
    path('api/contact/<int:pk>/', views.contact_detail_api, name='contact-detail-api'),
]