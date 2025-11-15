from groups.models import Kikoba
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, PasswordResetForm
from django.core.exceptions import ValidationError

User = get_user_model()


class PhonePasswordResetForm(PasswordResetForm):
    """Custom password reset form that uses phone number instead of email."""
    phone_number = forms.CharField(
        label="Phone Number",
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+255742178726',
            'autofocus': True
        }),
        help_text="Enter the phone number you used to register"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the email field from the parent form
        if 'email' in self.fields:
            del self.fields['email']
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        # Check if user with this phone number exists
        if not User.objects.filter(phone_number=phone_number).exists():
            raise ValidationError(
                "No account found with this phone number. Please check and try again."
            )
        return phone_number
    
    def get_users(self, phone_number):
        """Get users with the specified phone number."""
        active_users = User.objects.filter(
            phone_number__iexact=phone_number,
            is_active=True,
        )
        return (u for u in active_users if u.has_usable_password())
    
    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=None,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):
        """
        Generate a one-use only link for resetting password and send it to the user.
        We're using phone number instead of email for user lookup.
        """
        phone_number = self.cleaned_data["phone_number"]
        for user in self.get_users(phone_number):
            # For now, we'll use email if available, otherwise skip email sending
            # In production, you'd integrate with an SMS service here
            if user.email:
                # Use parent's save method to send email
                context = {
                    'email': user.email,
                    'domain': domain_override or request.get_host() if request else '',
                    'site_name': 'Mangi Vikoba+',
                    'uid': user.pk,
                    'user': user,
                    'token': token_generator.make_token(user) if token_generator else '',
                    'protocol': 'https' if use_https else 'http',
                }
                if extra_email_context:
                    context.update(extra_email_context)
                
                self.send_mail(
                    subject_template_name, email_template_name, context, from_email,
                    user.email, html_email_template_name=html_email_template_name,
                )

class PINSetPasswordForm(SetPasswordForm):
    """Custom password reset form that enforces 4-digit PIN."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove default password validators
        self.fields['new_password1'].validators = []
        self.fields['new_password2'].validators = []
        
    new_password1 = forms.CharField(
        label="New 4-Digit PIN",
        min_length=4,
        max_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'maxlength': '4',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric',
            'placeholder': '••••',
            'autocomplete': 'new-password'
        }),
        help_text="Enter your new 4-digit PIN"
    )
    new_password2 = forms.CharField(
        label="Confirm New PIN",
        min_length=4,
        max_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'maxlength': '4',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric',
            'placeholder': '••••',
            'autocomplete': 'new-password'
        }),
        help_text="Re-enter your new PIN to confirm"
    )
    
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if password:
            # Validate that password is exactly 4 digits
            if not password.isdigit():
                raise ValidationError("PIN must contain only numbers (0-9)")
            if len(password) != 4:
                raise ValidationError("PIN must be exactly 4 digits")
        return password
        
    def save(self, commit=True):
        # Override save to ensure the password is properly set
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user

class PINAuthenticationForm(AuthenticationForm):
    """Custom authentication form using 4-digit PIN instead of password."""
    username = forms.CharField(
        label="Phone Number",
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label="4-Digit PIN",
        min_length=4,
        max_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'maxlength': '4',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric',
            'placeholder': '••••'
        }),
        help_text="Enter your 4-digit PIN"
    )
    
    error_messages = {
        'invalid_login': (
            "Please enter a correct phone number and PIN. Note that both "
            "fields are case-sensitive."
        ),
        'inactive': "This account is inactive.",
    }

class KikobaRegistrationForm(forms.Form):
    admin_phone_number = forms.CharField(max_length=15, label="Your Phone Number")
    kikoba_name = forms.CharField(max_length=255, label="Kikoba Name")
    kikoba_description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label="Kikoba Description")
    location = forms.CharField(max_length=255, required=False, label="Location")
    estimated_members = forms.ChoiceField(choices=Kikoba.ESTIMATED_MEMBERS_CHOICES, required=False, label="Estimated Number of Members")
    constitution_document = forms.FileField(required=False, label="Constitution Document")
    other_documents = forms.FileField(required=False, label="Other Documents")

    def clean_admin_phone_number(self):
        phone_number = self.cleaned_data.get('admin_phone_number')
        if User.objects.filter(phone_number=phone_number).exists():
            raise ValidationError("A user with this phone number already exists. Please log in or use a different number.")
        return phone_number

    def clean_kikoba_name(self):
        name = self.cleaned_data.get('kikoba_name')
        if Kikoba.objects.filter(name=name).exists():
            raise ValidationError("A Kikoba with this name already exists.")
        return name



class MemberRegistrationForm(forms.Form):
    name = forms.CharField(max_length=100, label="Full Name")
    phone_number = forms.CharField(max_length=15, label="Phone Number")
    nida_number = forms.CharField(max_length=30, label="NIDA Number", required=False)  # Added NIDA Number
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'maxlength': '4', 'pattern': '[0-9]{4}', 'inputmode': 'numeric'}), 
        label="4-Digit PIN",
        min_length=4,
        max_length=4,
        help_text="Enter a 4-digit PIN (like an ATM card)"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'maxlength': '4', 'pattern': '[0-9]{4}', 'inputmode': 'numeric'}), 
        label="Confirm 4-Digit PIN",
        min_length=4,
        max_length=4
    )
    kikoba_numbers = forms.CharField(max_length=255, label="Kikoba Numbers", help_text="Enter the Kikoba number(s) you wish to join, separated by commas")
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            # Validate that password is exactly 4 digits
            if not password.isdigit():
                raise ValidationError("PIN must contain only numbers (0-9)")
            if len(password) != 4:
                raise ValidationError("PIN must be exactly 4 digits")
        return password

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if User.objects.filter(phone_number=phone_number).exists():
            raise ValidationError("A user with this phone number already exists.")
        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        kikoba_numbers = cleaned_data.get('kikoba_numbers', '').split(',')
        valid_numbers = []
        invalid_numbers = []
        
        for number in kikoba_numbers:
            number = number.strip()
            if number:
                if Kikoba.objects.filter(kikoba_number=number).exists():
                    valid_numbers.append(number)
                else:
                    invalid_numbers.append(number)
        
        if invalid_numbers:
            self.add_error('kikoba_numbers', f"These Kikoba numbers were not found: {', '.join(invalid_numbers)}")
        
        cleaned_data['valid_kikoba_numbers'] = valid_numbers
        return cleaned_data