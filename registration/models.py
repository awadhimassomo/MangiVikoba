from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import random
from datetime import timedelta

class UserManager(BaseUserManager):
    def create_user(self, phone_number, name, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Users must have a phone number')
        if not name:
            raise ValueError('Users must have a name')

        user = self.model(
            phone_number=phone_number,
            name=name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(phone_number, name, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('kikoba_admin', 'Kikoba Admin'),
        ('accountant', 'Accountant'),
    )
    
    phone_number = models.CharField(max_length=15, unique=True) # This is the USERNAME_FIELD
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='member')
    
    nida_number = models.CharField(max_length=30, blank=True, null=True, unique=True, help_text="National ID number, if available.")
    phone_number_verified = models.BooleanField(default=False)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    verification_method = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., NIDA, PHONE_PHOTO_MEMBER_VERIFIED")
    verification_status = models.CharField(max_length=20, default='pending', help_text="e.g., pending, verified, rejected")

    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['name'] # For createsuperuser: name is required in addition to phone_number
    
    def save(self, *args, **kwargs):
        if self.role == 'kikoba_admin':
            self.is_staff = True
        else:
            self.is_staff = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.phone_number})" # Simplified __str__


class PasswordResetOTP(models.Model):
    """Model to store OTP for password reset via phone number."""
    phone_number = models.CharField(max_length=15, db_index=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', '-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # OTP expires in 10 minutes
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if OTP is still valid (not expired and not used)."""
        return (
            not self.is_used and 
            timezone.now() < self.expires_at and 
            self.attempts < 5  # Max 5 attempts
        )
    
    @staticmethod
    def generate_otp():
        """Generate a random 6-digit OTP."""
        return str(random.randint(100000, 999999))
    
    @classmethod
    def create_otp(cls, phone_number):
        """Create a new OTP for the given phone number."""
        # Invalidate any existing OTPs for this phone number
        cls.objects.filter(
            phone_number=phone_number,
            is_used=False
        ).update(is_used=True)
        
        # Create new OTP
        otp = cls(
            phone_number=phone_number,
            otp=cls.generate_otp()
        )
        otp.save()
        return otp
    
    def __str__(self):
        return f"OTP for {self.phone_number} - {'Valid' if self.is_valid() else 'Invalid'}"
