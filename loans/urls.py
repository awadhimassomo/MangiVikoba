from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoanViewSet, RepaymentViewSet, LoanApplicationViewSet, LoanProductViewSet  # Added LoanProductViewSet

router = DefaultRouter()
router.register(r'loans', LoanViewSet, basename='loan')
router.register(r'repayments', RepaymentViewSet, basename='repayment')  # Renamed from loan-repayments or similar
router.register(r'applications', LoanApplicationViewSet, basename='loanapplication')
router.register(r'products', LoanProductViewSet, basename='loanproduct')  # Registered LoanProductViewSet

urlpatterns = [
    path('', include(router.urls)),
]
