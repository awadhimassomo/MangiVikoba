from django.db import models
from groups.models import Kikoba
from django.conf import settings

# Create your models here.

class PolicyLink(models.Model):
    kikoba = models.ForeignKey(Kikoba, on_delete=models.CASCADE, related_name='policy_links')
    title = models.CharField(max_length=200)
    url = models.URLField(max_length=500)
    description = models.TextField(blank=True, null=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.kikoba.name})"

    class Meta:
        ordering = ['-created_at']
