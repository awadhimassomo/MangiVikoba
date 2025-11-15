from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LearningCategoryViewSet, LearningContentViewSet, UserContentProgressViewSet

router = DefaultRouter()
router.register(r'categories', LearningCategoryViewSet, basename='learning-category')
router.register(r'content', LearningContentViewSet, basename='learning-content')
router.register(r'progress', UserContentProgressViewSet, basename='content-progress')

urlpatterns = [
    path('', include(router.urls)),
]
