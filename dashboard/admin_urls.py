from django.urls import path
from . import admin_views

app_name = 'super_admin'

urlpatterns = [
    # Main dashboard
    path('', admin_views.super_admin_dashboard, name='dashboard'),
    
    # Investment management
    path('investments/', admin_views.investment_list, name='investment_list'),
    path('investments/create/', admin_views.investment_create, name='investment_create'),
    path('investments/<int:investment_id>/', admin_views.investment_detail, name='investment_detail'),
    path('investments/<int:investment_id>/edit/', admin_views.investment_edit, name='investment_edit'),
    
    # Vikoba management
    path('vikoba/', admin_views.vikoba_management, name='vikoba_management'),
    path('vikoba/<int:kikoba_id>/', admin_views.vikoba_detail, name='vikoba_detail'),
    
    # User management
    path('users/', admin_views.user_management, name='user_management'),
    
    # System notifications
    path('notifications/', admin_views.system_notifications, name='notifications'),
    
    # System configuration
    path('configuration/', admin_views.system_configuration, name='configuration'),
    
    # Audit logs
    path('audit-logs/', admin_views.audit_logs, name='audit_logs'),
    
    # Reports & Analytics
    path('reports/', admin_views.reports_analytics, name='reports'),
]
