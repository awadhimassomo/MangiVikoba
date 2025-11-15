from django.db import models
from django.conf import settings
from django.utils import timezone
from groups.models import Kikoba


class Investment(models.Model):
    """System-wide investment opportunities managed by top-level admins"""
    INVESTMENT_TYPE_CHOICES = [
        ('agriculture', 'Agriculture'),
        ('livestock', 'Livestock'),
        ('real_estate', 'Real Estate'),
        ('business', 'Business'),
        ('technology', 'Technology'),
        ('manufacturing', 'Manufacturing'),
        ('bonds', 'Bonds'),
        ('treasury_bills', 'Treasury Bills'),
        ('stocks', 'Stocks & Securities'),
        ('mutual_funds', 'Mutual Funds'),
        ('fixed_deposits', 'Fixed Deposits'),
        ('microfinance', 'Microfinance'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('completed', 'Completed'),
    ]
    
    RISK_LEVEL_CHOICES = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
    ]
    
    title = models.CharField(max_length=255, help_text="Name of the investment opportunity")
    description = models.TextField(help_text="Brief description of the investment")
    investment_type = models.CharField(max_length=50, choices=INVESTMENT_TYPE_CHOICES, help_text="Type of investment")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', help_text="Current status of the investment")
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='medium', help_text="Risk level of the investment")
    
    # Core investment details
    ticker_symbol = models.CharField(max_length=20, blank=True, null=True, help_text="Ticker symbol if publicly traded")
    core_objective = models.TextField(blank=True, null=True, help_text="Core investment objective")
    current_price = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Current price per unit/share")
    time_horizon = models.CharField(max_length=20, blank=True, null=True, help_text="Expected investment time horizon")
    
    # Detailed information
    investment_thesis = models.TextField(blank=True, null=True, help_text="Detailed investment thesis and analysis")
    key_metrics = models.TextField(blank=True, null=True, help_text="Key financial metrics (one per line)")
    strengths = models.TextField(blank=True, null=True, help_text="Key strengths (one per line)")
    risks = models.TextField(blank=True, null=True, help_text="Key risks (one per line)")
    source_url = models.URLField(blank=True, null=True, help_text="Source URL for more information")
    internal_notes = models.TextField(blank=True, null=True, help_text="Internal notes (not visible to users)")
    
    # Financial details
    minimum_amount = models.DecimalField(max_digits=15, decimal_places=2)
    maximum_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    target_amount = models.DecimalField(max_digits=15, decimal_places=2)
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    expected_return_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Annual return rate in percentage")
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    duration_months = models.PositiveIntegerField(help_text="Investment duration in months")
    
    # Additional info
    location = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='investments/', blank=True, null=True)
    documents = models.FileField(upload_to='investment_documents/', blank=True, null=True)
    
    # Tracking
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_investments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Eligibility
    available_to_all_vikoba = models.BooleanField(default=True)
    specific_vikoba = models.ManyToManyField(Kikoba, blank=True, related_name='available_investments')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def progress_percentage(self):
        if self.target_amount > 0:
            return (self.current_amount / self.target_amount) * 100
        return 0
    
    @property
    def is_active(self):
        return self.status == 'active' and self.start_date <= timezone.now().date() <= self.end_date


class InvestmentDocument(models.Model):
    """Model to store multiple documents for an investment"""
    DOCUMENT_TYPES = [
        ('prospectus', 'Prospectus'),
        ('financials', 'Financial Statements'),
        ('legal', 'Legal Documents'),
        ('other', 'Other'),
    ]
    
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name='investment_documents')
    document = models.FileField(upload_to='investment_documents/%Y/%m/%d/')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='other')
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.title or f"Document {self.id} for {self.investment.title}"
    
    @property
    def filename(self):
        return os.path.basename(self.document.name)


class InvestmentParticipation(models.Model):
    """Track which vikoba participate in which investments"""
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name='participations')
    kikoba = models.ForeignKey(Kikoba, on_delete=models.CASCADE, related_name='investment_participations')
    amount_invested = models.DecimalField(max_digits=15, decimal_places=2)
    invested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ], default='pending')
    
    returns_received = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('investment', 'kikoba')
        ordering = ['-invested_at']
    
    def __str__(self):
        return f"{self.kikoba.name} - {self.investment.title}"


class SystemConfiguration(models.Model):
    """System-wide configuration settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"


class SystemNotification(models.Model):
    """System-wide notifications from admins to all users or specific vikoba"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Targeting
    send_to_all = models.BooleanField(default=False)
    specific_vikoba = models.ManyToManyField(Kikoba, blank=True, related_name='system_notifications')
    
    # Scheduling
    scheduled_for = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class AuditLog(models.Model):
    """Track all admin actions for accountability"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} at {self.timestamp}"
