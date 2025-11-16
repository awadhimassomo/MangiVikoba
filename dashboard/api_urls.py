from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .api_views import InvestmentViewSet
from .user_api_views import (
    UserLoansView, UserLoanDetailView, UserRepaymentsView,
    UserSavingsView, UserSavingsTransactionsView, UserDashboardSummaryView
)
from .kikoba_api_views import KikobaMemberLoansView, KikobaMemberLoanDetailView
from .kikoba_contributions_views import KikobaMemberContributionsView

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'investments', InvestmentViewSet, basename='investment')

# User-specific API endpoints
user_urlpatterns = [
    # Loans
    path('loans/', UserLoansView.as_view(), name='user-loans'),
    path('loans/<int:loan_id>/', UserLoanDetailView.as_view(), name='user-loan-detail'),
    path('loans/<int:loan_id>/repayments/', UserRepaymentsView.as_view(), name='user-loan-repayments'),
    
    # Savings
    path('savings/', UserSavingsView.as_view(), name='user-savings'),
    path('savings/transactions/', UserSavingsTransactionsView.as_view(), name='user-savings-transactions'),
    
    # Dashboard
    path('dashboard/summary/', UserDashboardSummaryView.as_view(), name='user-dashboard-summary'),
]

# Kikoba member endpoints
kikoba_urlpatterns = [
    # Member loans
    path('<int:kikoba_id>/members/<int:member_id>/loans/', KikobaMemberLoansView.as_view(), name='kikoba-member-loans'),
    path('<int:kikoba_id>/members/<int:member_id>/loans/<int:loan_id>/', KikobaMemberLoanDetailView.as_view(), name='kikoba-member-loan-detail'),
    
    # Member contributions
    path('<int:kikoba_id>/members/<int:member_id>/contributions/', KikobaMemberContributionsView.as_view(), name='kikoba-member-contributions'),
]

# The API URLs are now determined automatically by the router
urlpatterns = [
    # User-specific endpoints (require authentication)
    path('me/', include((user_urlpatterns, 'user'), namespace='user')),
    
    # Kikoba-specific endpoints
    path('kikobas/', include((kikoba_urlpatterns, 'kikoba'), namespace='kikoba')),
    
    # Other API endpoints
    path('', include(router.urls)),
    
    # JWT Token refresh
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
