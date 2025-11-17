from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model, logout # Added logout here
from django.contrib import messages
from django.urls import reverse
from django.views import View
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, UserSerializer, UpdateUserSerializer
from .forms import KikobaRegistrationForm, MemberRegistrationForm, PINSetPasswordForm
from .models import PasswordResetOTP
from groups.models import Kikoba, KikobaMembership, KikobaInvitation
from sms.utils import send_sms

User = get_user_model()

def unified_registration(request):
    kikoba_form = KikobaRegistrationForm(request.POST or None, request.FILES or None, prefix='kikoba')
    member_form = MemberRegistrationForm(request.POST or None, prefix='member')
    
    if request.method == 'POST':
        if 'register_kikoba' in request.POST:
            if kikoba_form.is_valid():
                phone_number = kikoba_form.cleaned_data['admin_phone_number']
                group_type = kikoba_form.cleaned_data.get('group_type', 'standard')
                
                # Debug: Print the group_type to console (you can remove this after testing)
                print(f"DEBUG: Group Type from form: {group_type}")
                
                # Create the Kikoba instance with the creator's phone number
                kikoba = Kikoba(
                    name=kikoba_form.cleaned_data['kikoba_name'],
                    description=kikoba_form.cleaned_data['kikoba_description'],
                    location=kikoba_form.cleaned_data['location'],
                    estimated_members=kikoba_form.cleaned_data['estimated_members'],
                    group_type=group_type,
                    creator_phone_number=phone_number  # Store the creator's phone number
                )
                if kikoba_form.cleaned_data.get('constitution_document'):
                    kikoba.constitution_document = kikoba_form.cleaned_data['constitution_document']
                kikoba.save()
                
                # Debug: Verify it was saved
                print(f"DEBUG: Kikoba saved with group_type: {kikoba.group_type}")

                # Handle multiple file uploads for other_documents
                other_docs = request.FILES.getlist('kikoba-other_documents')
                if other_docs:
                    # For now, we'll just save the first file to the single FileField
                    # In a real implementation, you might want to create a separate model for document storage
                    kikoba.other_documents = other_docs[0]
                    kikoba.save()
                    
                    # If you need to store multiple files, you would typically do something like:
                    # for doc in other_docs:
                    #     Document.objects.create(kikoba=kikoba, file=doc)

                # Send SMS notification with the new Kikoba number
                phone_number = kikoba_form.cleaned_data['admin_phone_number']
                message = f"Hongera! Kikoba chako '{kikoba.name}' kimesajiliwa. Namba ya kikoba ni {kikoba.kikoba_number}. Tumia namba hii kumaliza usajili wako."
                send_sms(phone_number, message)

                # Pre-fill the member form with the new Kikoba number and phone number
                initial_data = {
                    'kikoba_numbers': kikoba.kikoba_number,
                    'phone_number': phone_number
                }
                member_form = MemberRegistrationForm(initial=initial_data, prefix='member')

                messages.info(request, f"Kikoba '{kikoba.name}' created successfully! Please create your administrator account below.")

                return render(request, 'registration/unified_register.html', {
                    'kikoba_form': KikobaRegistrationForm(prefix='kikoba'),
                    'member_form': member_form
                })

        elif 'register_member' in request.POST:
            if member_form.is_valid():
                phone_number = member_form.cleaned_data['phone_number']
                password = member_form.cleaned_data['password']

                # Create the user first
                user = User.objects.create_user(
                    phone_number=phone_number,
                    password=password,
                    name=member_form.cleaned_data['name'],
                    nida_number=member_form.cleaned_data.get('nida_number')
                )

                # Associate user with Kikobas and determine their role
                for kikoba_number in member_form.cleaned_data['valid_kikoba_numbers']:
                    kikoba = Kikoba.objects.get(kikoba_number=kikoba_number)
                    
                    # Check if this user is the creator of the kikoba
                    if kikoba.creator_phone_number == user.phone_number:
                        role = 'chairperson'
                        # Now that the user exists, link them as the creator
                        kikoba.created_by = user
                        kikoba.creator_phone_number = None  # Clean up the temporary field
                        kikoba.save()
                    else:
                        role = 'member'

                    # Check if user was invited (has pending invitation)
                    pending_invitation = KikobaInvitation.objects.filter(
                        kikoba=kikoba,
                        email_or_phone=user.phone_number,
                        status='pending'
                    ).first()
                    
                    # Auto-approve if invited, otherwise pending approval
                    if pending_invitation:
                        # Invited member - auto-approve
                        membership, created = KikobaMembership.objects.get_or_create(
                            user=user,
                            kikoba=kikoba,
                            defaults={'role': role, 'is_active': True}
                        )
                        
                        # Mark invitation as accepted
                        pending_invitation.status = 'accepted'
                        pending_invitation.save()
                    else:
                        # Self-registered - pending approval
                        membership, created = KikobaMembership.objects.get_or_create(
                            user=user,
                            kikoba=kikoba,
                            defaults={'role': role, 'is_active': False}  # Pending approval
                        )
                
                # Log the user in
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                messages.success(request, "Registration complete! You are now logged in.")
                return redirect(reverse('dashboard:home'))
    
    return render(request, 'registration/unified_register.html', {
        'kikoba_form': kikoba_form,
        'member_form': member_form
    })

from django.shortcuts import redirect
from django.urls import reverse

def custom_logout(request):
    """Custom logout view that redirects to the login page"""
    logout(request)
    return redirect(reverse('login'))

# Remove or comment out the old views if they are no longer needed
# def registration_choice(request):
#     return render(request, 'registration/registration_choice.html')
# 
# def register_kikoba(request):
#     # ... old code ...
#     pass
# 
# def register_member(request):
#     # ... old code ...
#     pass

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user


class UpdateUserProfileView(generics.UpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UpdateUserSerializer
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)


# OTP-Based Password Reset Views

class PasswordResetRequestOTPView(View):
    """Step 1: User enters phone number, system generates and sends OTP."""
    
    def get(self, request):
        return render(request, 'registration/password_reset_request.html')
    
    def post(self, request):
        phone_number = request.POST.get('phone_number', '').strip()
        
        # Validate phone number
        if not phone_number:
            messages.error(request, 'Please enter your phone number.')
            return render(request, 'registration/password_reset_request.html')
        
        # Check if user exists
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            messages.error(request, 'No account found with this phone number.')
            return render(request, 'registration/password_reset_request.html')
        
        # Generate and save OTP
        otp_instance = PasswordResetOTP.create_otp(phone_number)
        
        # Send OTP via SMS (for now, we'll display it in development)
        try:
            message = f"Your Mangi Vikoba+ PIN reset code is: {otp_instance.otp}. Valid for 10 minutes."
            send_sms(phone_number, message)
            messages.success(request, f'OTP has been sent to {phone_number}')
        except Exception as e:
            # In development, show the OTP in messages
            messages.info(request, f'[DEV MODE] Your OTP is: {otp_instance.otp}')
        
        # Store phone number in session for next step
        request.session['reset_phone_number'] = phone_number
        request.session['otp_sent_at'] = timezone.now().isoformat()
        
        return redirect('password_reset_verify_otp')


class PasswordResetVerifyOTPView(View):
    """Step 2: User enters OTP to verify."""
    
    def get(self, request):
        phone_number = request.session.get('reset_phone_number')
        if not phone_number:
            messages.error(request, 'Session expired. Please start over.')
            return redirect('password_reset_request')
        
        return render(request, 'registration/password_reset_verify_otp.html', {
            'phone_number': phone_number
        })
    
    def post(self, request):
        phone_number = request.session.get('reset_phone_number')
        if not phone_number:
            messages.error(request, 'Session expired. Please start over.')
            return redirect('password_reset_request')
        
        otp_entered = request.POST.get('otp', '').strip()
        
        if not otp_entered:
            messages.error(request, 'Please enter the OTP.')
            return render(request, 'registration/password_reset_verify_otp.html', {
                'phone_number': phone_number
            })
        
        # Get the latest valid OTP for this phone number
        try:
            otp_instance = PasswordResetOTP.objects.filter(
                phone_number=phone_number,
                is_used=False
            ).latest('created_at')
        except PasswordResetOTP.DoesNotExist:
            messages.error(request, 'No valid OTP found. Please request a new one.')
            return redirect('password_reset_request')
        
        # Increment attempts
        otp_instance.attempts += 1
        otp_instance.save()
        
        # Verify OTP
        if not otp_instance.is_valid():
            messages.error(request, 'OTP has expired or exceeded maximum attempts. Please request a new one.')
            return redirect('password_reset_request')
        
        if otp_instance.otp != otp_entered:
            remaining_attempts = 5 - otp_instance.attempts
            if remaining_attempts > 0:
                messages.error(request, f'Invalid OTP. {remaining_attempts} attempts remaining.')
            else:
                messages.error(request, 'Maximum attempts exceeded. Please request a new OTP.')
                return redirect('password_reset_request')
            
            return render(request, 'registration/password_reset_verify_otp.html', {
                'phone_number': phone_number
            })
        
        # OTP is valid - mark as used
        otp_instance.is_used = True
        otp_instance.save()
        
        # Store verification in session
        request.session['otp_verified'] = True
        request.session['otp_verified_at'] = timezone.now().isoformat()
        
        messages.success(request, 'OTP verified successfully! You can now reset your PIN.')
        return redirect('password_reset_change_pin')


class PasswordResetChangePINView(View):
    """Step 3: After OTP verification, user can change their PIN."""
    
    def get(self, request):
        # Check if OTP was verified
        if not request.session.get('otp_verified'):
            messages.error(request, 'Please verify OTP first.')
            return redirect('password_reset_request')
        
        phone_number = request.session.get('reset_phone_number')
        if not phone_number:
            messages.error(request, 'Session expired. Please start over.')
            return redirect('password_reset_request')
        
        # Get user
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('password_reset_request')
        
        form = PINSetPasswordForm(user=user)
        return render(request, 'registration/password_reset_change_pin.html', {
            'form': form,
            'phone_number': phone_number
        })
    
    def post(self, request):
        # Check if OTP was verified
        if not request.session.get('otp_verified'):
            messages.error(request, 'Please verify OTP first.')
            return redirect('password_reset_request')
        
        phone_number = request.session.get('reset_phone_number')
        if not phone_number:
            messages.error(request, 'Session expired. Please start over.')
            return redirect('password_reset_request')
        
        # Get user
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('password_reset_request')
        
        form = PINSetPasswordForm(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            
            # Clear session data
            request.session.pop('reset_phone_number', None)
            request.session.pop('otp_verified', None)
            request.session.pop('otp_verified_at', None)
            request.session.pop('otp_sent_at', None)
            
            messages.success(request, 'Your PIN has been reset successfully! You can now log in with your new PIN.')
            return redirect('login')
        
        return render(request, 'registration/password_reset_change_pin.html', {
            'form': form,
            'phone_number': phone_number
        })
