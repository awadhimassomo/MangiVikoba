from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SavingViewSet, KikobaBalanceViewSet, MemberBalanceViewSet  # Renamed GroupBalanceViewSet

router = DefaultRouter()
router.register(r'savings', SavingViewSet, basename='saving')
router.register(r'kikoba-balances', KikobaBalanceViewSet, basename='kikoba-balance')  # Renamed from group-balances and GroupBalanceViewSet
router.register(r'member-balances', MemberBalanceViewSet, basename='member-balance')

urlpatterns = [
    path('', include(router.urls)),
]
