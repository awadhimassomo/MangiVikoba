from django.db import models
from django.conf import settings
from django.utils import timezone

class LearningCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Learning Categories"
    
    def __str__(self):
        return self.name

class LearningContent(models.Model):
    TYPE_CHOICES = (
        ('article', 'Article'),
        ('video', 'Video'),
        ('audio', 'Audio'),
    )
    
    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('sw', 'Swahili'),
    )
    
    title = models.CharField(max_length=255)
    content_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    category = models.ForeignKey(LearningCategory, on_delete=models.CASCADE, related_name='content')
    
    # For articles
    content_text = models.TextField(blank=True)
    
    # For media (video/audio)
    media_url = models.URLField(blank=True)
      # For all types
    summary = models.TextField()
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_content')
    created_at = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_content_type_display()}, {self.get_language_display()})"
    
    def save(self, *args, **kwargs):
        # Send notification about new content
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Only send notifications for newly published content
        if is_new and self.is_published:
            from notifications.models import Notification
            from registration.models import User
            
            # Get all users
            users = User.objects.filter(is_active=True)
            
            # Create notification for each user
            for user in users:
                Notification.objects.create(
                    user=user,
                    type='new_learning_content',
                    title=f"New {self.get_content_type_display()}: {self.title}",
                    message=f"New learning content has been added: {self.title} in {self.category.name} category."
                )

class UserContentProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='learning_progress')
    content = models.ForeignKey(LearningContent, on_delete=models.CASCADE, related_name='user_progress')
    is_read = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'content')
    
    def __str__(self):
        status = "Completed" if self.is_completed else ("Read" if self.is_read else "Not started")
        return f"{self.user.name} - {self.content.title}: {status}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def mark_as_completed(self):
        if not self.is_completed:
            self.is_read = True
            self.is_completed = True
            self.read_at = self.read_at or timezone.now()
            self.completed_at = timezone.now()
            self.save()
