from rest_framework import serializers
from .models import LearningCategory, LearningContent, UserContentProgress
from django.contrib.auth import get_user_model

User = get_user_model()

class LearningCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningCategory
        fields = ('id', 'name', 'description')

class LearningContentSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    content_type_display = serializers.SerializerMethodField()
    language_display = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningContent
        fields = (
            'id', 'title', 'content_type', 'content_type_display', 'language', 
            'language_display', 'category', 'category_name', 'content_text', 
            'media_url', 'summary', 'created_by', 'created_by_name', 
            'created_at', 'is_published', 'user_progress'
        )
        read_only_fields = ('id', 'created_by', 'created_at', 'user_progress')
    
    def get_category_name(self, obj):
        return obj.category.name
    
    def get_created_by_name(self, obj):
        return obj.created_by.name
    
    def get_content_type_display(self, obj):
        return obj.get_content_type_display()
    
    def get_language_display(self, obj):
        return obj.get_language_display()
    
    def get_user_progress(self, obj):
        user = self.context.get('request').user
        try:
            progress = UserContentProgress.objects.get(user=user, content=obj)
            return {
                'is_read': progress.is_read,
                'is_completed': progress.is_completed,
                'read_at': progress.read_at,
                'completed_at': progress.completed_at
            }
        except UserContentProgress.DoesNotExist:
            return {
                'is_read': False,
                'is_completed': False,
                'read_at': None,
                'completed_at': None
            }
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        return super().create(validated_data)

class UserContentProgressSerializer(serializers.ModelSerializer):
    content_title = serializers.SerializerMethodField()
    
    class Meta:
        model = UserContentProgress
        fields = ('id', 'user', 'content', 'content_title', 'is_read', 'is_completed', 'read_at', 'completed_at')
        read_only_fields = ('id', 'user', 'read_at', 'completed_at')
    
    def get_content_title(self, obj):
        return obj.content.title
