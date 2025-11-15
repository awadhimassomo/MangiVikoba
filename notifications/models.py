from django.db import models
from django.conf import settings
from django.utils import timezone
from groups.models import Kikoba # Import Kikoba

class Notification(models.Model):
    TYPE_CHOICES = (
        ('contribution_due', 'Contribution Due'),
        ('loan_repayment_due', 'Loan Repayment Due'),
        ('loan_approved', 'Loan Approved'),
        ('loan_rejected', 'Loan Rejected'),
        ('saving_confirmed', 'Saving Confirmed'),
        ('group_invitation', 'Group Invitation'), # Keep as group_invitation for now, or consider renaming to kikoba_invitation
        ('group_announcement', 'Group Announcement'), # Keep as group_announcement for now, or consider renaming to kikoba_announcement
        ('new_learning_content', 'New Learning Content'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    kikoba = models.ForeignKey(Kikoba, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications') # Added kikoba field
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        if self.kikoba:
            return f"{self.title} - {self.user.name} ({self.kikoba.name})"
        return f"{self.title} - {self.user.name}"

class Announcement(models.Model):
    kikoba = models.ForeignKey(Kikoba, on_delete=models.CASCADE, related_name='announcements', null=True, blank=True) # MODIFIED: Added null=True, blank=True
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_announcements')
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.title} - {self.kikoba.name}" # Updated to use kikoba.name
    
    def save(self, *args, **kwargs):
        # Create a notification for each group member when an announcement is made
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            from groups.models import KikobaMembership # Import KikobaMembership
            
            # Get all active members of the group
            members = KikobaMembership.objects.filter(kikoba=self.kikoba, is_active=True) # Updated to use kikoba
            
            # Create a notification for each member
            for membership in members:
                Notification.objects.create(
                    user=membership.user,
                    kikoba=self.kikoba, # Pass kikoba object
                    type='group_announcement', # Consider renaming to kikoba_announcement
                    title=self.title,
                    message=self.message
                )

class ScheduledReminder(models.Model):
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
    )
    
    TYPE_CHOICES = (
        ('contribution', 'Contribution Due'),
        ('loan_repayment', 'Loan Repayment Due'),
    )
    
    kikoba = models.ForeignKey(Kikoba, on_delete=models.CASCADE, related_name='scheduled_reminders', null=True, blank=True) # MODIFIED: Added null=True, blank=True
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    day_of_week = models.PositiveIntegerField(null=True, blank=True)  # 0=Monday, 6=Sunday
    day_of_month = models.PositiveIntegerField(null=True, blank=True)  # 1-31
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.get_type_display()} reminder for {self.kikoba.name} ({self.get_frequency_display()})" # Updated to use kikoba.name
