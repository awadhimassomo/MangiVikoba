from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    api_root,
    CustomTokenObtainPairView,
    UserViewSet, KikobaViewSet, KikobaMembershipViewSet,
    KikobaInvitationViewSet, SavingViewSet, ContributionViewSet,
    MemberBalanceViewSet, KikobaBalanceViewSet, SavingCycleViewSet,
    LoanProductViewSet, LoanApplicationViewSet, LoanViewSet,
    RepaymentViewSet, NotificationViewSet, EntryFeePaymentViewSet,
    ShareContributionViewSet, EmergencyFundContributionViewSet
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'vikoba', KikobaViewSet, basename='kikoba')
router.register(r'memberships', KikobaMembershipViewSet, basename='membership')
router.register(r'invitations', KikobaInvitationViewSet, basename='invitation')
router.register(r'savings', SavingViewSet, basename='saving')
router.register(r'contributions', ContributionViewSet, basename='contribution')
router.register(r'member-balances', MemberBalanceViewSet, basename='member-balance')
router.register(r'kikoba-balances', KikobaBalanceViewSet, basename='kikoba-balance')
router.register(r'saving-cycles', SavingCycleViewSet, basename='saving-cycle')
router.register(r'loan-products', LoanProductViewSet, basename='loan-product')
router.register(r'loan-applications', LoanApplicationViewSet, basename='loan-application')
router.register(r'loans', LoanViewSet, basename='loan')
router.register(r'repayments', RepaymentViewSet, basename='repayment')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'entry-fee-payments', EntryFeePaymentViewSet, basename='entry-fee-payment')
router.register(r'share-contributions', ShareContributionViewSet, basename='share-contribution')
router.register(r'emergency-fund-contributions', EmergencyFundContributionViewSet, basename='emergency-fund-contribution')

# The API URLs are determined automatically by the router
urlpatterns = [
    # API Root - shows available endpoints
    path('', api_root, name='api-root'),
    
    # JWT Authentication endpoints
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API routes
    path('', include(router.urls)),
]
