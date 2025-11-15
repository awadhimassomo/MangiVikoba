from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet, ProfitDistributionViewSet

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'profit-distributions', ProfitDistributionViewSet, basename='profit-distribution')

urlpatterns = [
    path('', include(router.urls)),
]
