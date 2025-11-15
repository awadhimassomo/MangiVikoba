from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Updated view imports
from .views import KikobaViewSet, KikobaInvitationViewSet
from . import views # Import the views module

router = DefaultRouter()
router.register(r'vikoba', KikobaViewSet, basename='kikoba') # Changed from groups to vikoba, GroupViewSet to KikobaViewSet, basename group to kikoba
router.register(r'kikoba-invitations', KikobaInvitationViewSet, basename='kikoba-invitation') # Changed from invitations to kikoba-invitations, GroupInvitationViewSet to KikobaInvitationViewSet, basename invitation to kikoba-invitation

app_name = 'groups'

urlpatterns = [
    path('', include(router.urls)),
    path('<int:kikoba_id>/configure-contributions/', views.kikoba_contribution_config_view, name='kikoba_contribution_config'),

    # Entry Fee URLs
    path('<int:kikoba_id>/member/<int:member_id>/record-entry-fee/', views.record_entry_fee_payment, name='record_entry_fee_payment'),
    path('entry-fee-payment/<int:payment_id>/add-installment/', views.record_entry_fee_installment, name='record_entry_fee_installment'),

    # Share Contribution URLs
    path('<int:kikoba_id>/member/<int:member_id>/record-share/', views.record_share_contribution, name='record_share_contribution'),
    path('share-contribution/<int:contribution_id>/add-installment/', views.record_share_installment, name='record_share_installment'),

    # Savings URL
    path('<int:kikoba_id>/member/<int:member_id>/record-saving/', views.record_saving, name='record_saving'),

    # Emergency Fund URL
    path('<int:kikoba_id>/member/<int:member_id>/record-emergency-fund/', views.record_emergency_fund_contribution, name='record_emergency_fund_contribution'),
]
