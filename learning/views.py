from django.shortcuts import render
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import LearningCategory, LearningContent, UserContentProgress
from .serializers import LearningCategorySerializer, LearningContentSerializer, UserContentProgressSerializer
from django.utils import timezone

class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to create/edit learning content.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_staff or request.user.role == 'admin'

class LearningCategoryViewSet(viewsets.ModelViewSet):
    queryset = LearningCategory.objects.all()
    serializer_class = LearningCategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

class LearningContentViewSet(viewsets.ModelViewSet):
    serializer_class = LearningContentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'summary', 'content_text']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = LearningContent.objects.all()
        
        # Only staff can see unpublished content
        if not self.request.user.is_staff and self.request.user.role != 'admin':
            queryset = queryset.filter(is_published=True)
        
        # Filter by category if specified
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by language if specified
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language=language)
        
        # Filter by content_type if specified
        content_type = self.request.query_params.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        content = self.get_object()
        
        progress, created = UserContentProgress.objects.get_or_create(
            user=request.user,
            content=content
        )
        
        progress.mark_as_read()
        
        serializer = UserContentProgressSerializer(progress)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_completed(self, request, pk=None):
        content = self.get_object()
        
        progress, created = UserContentProgress.objects.get_or_create(
            user=request.user,
            content=content
        )
        
        progress.mark_as_completed()
        
        serializer = UserContentProgressSerializer(progress)
        return Response(serializer.data)

class UserContentProgressViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserContentProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserContentProgress.objects.filter(user=self.request.user)
