from django.contrib import admin
from .models import LearningCategory, LearningContent, UserContentProgress

@admin.register(LearningCategory)
class LearningCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')

@admin.register(LearningContent)
class LearningContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_type', 'language', 'category', 'created_by', 'is_published')
    list_filter = ('content_type', 'language', 'category', 'is_published')
    search_fields = ('title', 'summary', 'content_text')

@admin.register(UserContentProgress)
class UserContentProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'is_read', 'is_completed', 'read_at', 'completed_at')
    list_filter = ('is_read', 'is_completed')
    search_fields = ('user__name', 'content__title')
