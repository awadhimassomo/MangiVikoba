from django.urls import path, include
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Main entry points
    path('', views.dashboard_home, name='home'),
    path('kikoba-admin-dashboard/<int:kikoba_id>/', views.kikoba_admin_dashboard, name='kikoba_admin_dashboard'),
    path('member-dashboard/', views.member_dashboard, name='member_dashboard'),

    # Admin modules
    path('kikoba-admin/group-management/', views.group_management_view, name='group_management'),
    path('kikoba-admin/savings-contributions/', views.savings_contributions_view, name='savings_contributions'),
    path('kikoba-admin/loans-management/', views.kikoba_loans_management_view, name='kikoba_loans_management'),
    path('kikoba-admin/credit-score/', views.credit_score_engine_view, name='credit_score_engine'),
    path('kikoba-admin/auditing-reporting/', views.auditing_reporting_view, name='auditing_reporting'),
    path('kikoba-admin/learning-hub/', views.learning_hub_view, name='learning_hub'),

    # Generic pages & forms
    path('loans/', views.loan_management, name='loan_management'),
    path('loans/add/', views.add_loan_view, name='add_loan'),
    path('loans/application/<int:application_id>/', views.loan_application_detail_view, name='loan_application_detail'),
    path('loans/application/<int:application_id>/approve/', views.approve_loan_application, name='approve_loan_application'),
    path('loans/application/<int:application_id>/reject/', views.reject_loan_application, name='reject_loan_application'),
    path('members/', views.member_management, name='member_management'),
    path('members/add/', views.add_member_view, name='add_member'),
    path('entry-fees/', views.entry_fee_management, name='entry_fee_management'),
    path('share-contributions/', views.share_contributions_management, name='share_contributions_management'),
    path('savings/', views.savings_management, name='savings_management'),
    path('emergency-fund/', views.emergency_fund_management, name='emergency_fund_management'),
    path('interest/', views.interest_management, name='interest_management'),
    path('policies/', views.policy_management, name='policy_management'),
    path('settings/', views.settings_view, name='settings'),
    path('profile/', views.profile_view, name='profile'),
    path('emergency-funds/', views.emergency_funds_view, name='emergency_funds'),
    
    # Super Admin Panel
    path('super-admin/', include('dashboard.admin_urls')),
]
