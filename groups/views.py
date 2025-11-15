from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import (
    Kikoba, KikobaContributionConfig, KikobaMembership,
    EntryFeePayment, EntryFeeInstallment, ShareContribution,
    ShareInstallment, Saving, EmergencyFundContribution
)
from .forms import (
    KikobaContributionConfigForm, EntryFeePaymentForm, EntryFeeInstallmentForm,
    ShareContributionForm, ShareInstallmentForm, SavingForm, EmergencyFundContributionForm
)
from django.urls import reverse_lazy

from django.shortcuts import render
from django.db import models # Add this import for Q objects
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Kikoba, KikobaMembership, KikobaInvitation 
from .serializers import KikobaSerializer, KikobaMembershipSerializer, KikobaInvitationSerializer, KikobaCreateSerializer
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class IsKikobaAdmin(permissions.BasePermission): # Renamed from IsGroupAdmin
    """
    Custom permission to only allow kikoba admins to perform certain actions.
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Kikoba): # Changed from Group
            return KikobaMembership.objects.filter( # Changed from GroupMembership
                kikoba=obj, # Changed from group
                user=request.user,
                role__in=['chairperson', 'treasurer', 'kikoba_admin'] # Added kikoba_admin
            ).exists()
        return False

class KikobaViewSet(viewsets.ModelViewSet): # Renamed from GroupViewSet
    serializer_class = KikobaSerializer # Changed from GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Kikoba.objects.none()
        user_memberships = KikobaMembership.objects.filter(user=user, is_active=True) # Changed from GroupMembership
        return Kikoba.objects.filter(kikoba_memberships__in=user_memberships).distinct() # Changed from Group, memberships
    
    def get_serializer_class(self):
        if self.action == 'create':
            return KikobaCreateSerializer # Changed from GroupCreateSerializer
        return KikobaSerializer # Changed from GroupSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        kikoba = serializer.save()
        user = kikoba.created_by

        # Automatically create a membership for the creator
        KikobaMembership.objects.create(
            kikoba=kikoba,
            user=user,
            role='chairperson',
            is_active=True
        )

        response_data = {
            'message': f'Kikoba "{kikoba.name}" created successfully! You have been assigned as the chairperson.',
            'kikoba': KikobaSerializer(kikoba).data,
            'user': {
                'id': user.id,
                'name': user.name,
                'phone_number': user.phone_number
            }
        }

        return Response(response_data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        # This method is now effectively replaced by the logic in the serializer's create method
        pass

    @action(detail=True, methods=['post'], permission_classes=[IsKikobaAdmin]) # Changed from IsGroupAdmin
    def invite_member(self, request, pk=None):
        kikoba = self.get_object() # Changed from group
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        existing_invitation = KikobaInvitation.objects.filter( # Changed from GroupInvitation
            kikoba=kikoba, # Changed from group
            status='pending'
        ).first()
        # Adjusting to use email_or_phone as per model for KikobaInvitation
        if 'email_or_phone' in request.data:
             existing_invitation = KikobaInvitation.objects.filter(
                kikoba=kikoba,
                email_or_phone=request.data.get('email_or_phone'),
                status='pending'
            ).first()

        if existing_invitation:
            return Response({'error': 'Invitation already sent to this number/email'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Assuming phone_number is the primary identifier for User
            user_to_check = None
            if User.objects.filter(phone_number=phone_number).exists():
                 user_to_check = User.objects.get(phone_number=phone_number)
            elif 'email_or_phone' in request.data and User.objects.filter(email=request.data.get('email_or_phone')).exists():
                 user_to_check = User.objects.get(email=request.data.get('email_or_phone'))

            if user_to_check and KikobaMembership.objects.filter(kikoba=kikoba, user=user_to_check, is_active=True).exists(): # Changed
                return Response({'error': 'User is already a member of this kikoba'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            pass
        
        invitation = KikobaInvitation.objects.create( # Changed from GroupInvitation
            kikoba=kikoba, # Changed from group
            invited_by=request.user,
            email_or_phone=request.data.get('email_or_phone', phone_number) # Use email_or_phone
        )
        
        serializer = KikobaInvitationSerializer(invitation) # Changed from GroupInvitationSerializer
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        kikoba = self.get_object() # Changed from group
        memberships = KikobaMembership.objects.filter(kikoba=kikoba, is_active=True) # Changed
        serializer = KikobaMembershipSerializer(memberships, many=True) # Changed
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsKikobaAdmin]) # Changed
    def update_member_role(self, request, pk=None):
        kikoba = self.get_object() # Changed
        user_id = request.data.get('user_id')
        new_role = request.data.get('role')

        if not user_id or not new_role:
            return Response({'error': 'User ID and role are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            membership = KikobaMembership.objects.get(kikoba=kikoba, user_id=user_id) # Changed
            membership.role = new_role
            membership.save()
            serializer = KikobaMembershipSerializer(membership) # Changed
            return Response(serializer.data)
        except KikobaMembership.DoesNotExist: # Changed
            return Response({'error': 'Membership not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class KikobaInvitationViewSet(viewsets.ModelViewSet): # Renamed from GroupInvitationViewSet
    serializer_class = KikobaInvitationSerializer # Changed
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can see invitations sent to them (matching their phone/email if not yet a user)
        # or invitations for vikoba they are admins of.
        user = self.request.user
        # This part needs careful consideration based on how users accept invitations
        # For now, showing all invitations related to user's vikoba if they are admin, or sent by them.
        admin_kikoba_ids = KikobaMembership.objects.filter(user=user, role__in=['kikoba_admin', 'chairperson', 'treasurer']).values_list('kikoba_id', flat=True)
        
        # Invitations sent by the user OR for vikoba they administer OR to their phone/email
        # This is a simplified example; you might need more complex logic for matching non-users
        return KikobaInvitation.objects.filter(
            models.Q(invited_by=user) |
            models.Q(kikoba_id__in=admin_kikoba_ids) |
            models.Q(email_or_phone=user.phone_number) |
            models.Q(email_or_phone=user.email if user.email else "") # Handle if email is None
        ).distinct() # Changed

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        invitation = self.get_object()
        # ... (logic to check if invitation is for the request.user)
        # This needs to be robust, e.g. matching phone/email if user wasn't logged in when invited
        if not (invitation.email_or_phone == request.user.phone_number or 
                (request.user.email and invitation.email_or_phone == request.user.email)):
            return Response({"error": "This invitation is not for you."}, status=status.HTTP_403_FORBIDDEN)

        if invitation.status != 'pending':
            return Response({'error': 'Invitation already responded to'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create membership
        KikobaMembership.objects.create( # Changed
            kikoba=invitation.kikoba, # Changed
            user=request.user,
            role=invitation.role
        )
        invitation.status = 'accepted'
        invitation.save()
        return Response({'status': 'invitation accepted'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        invitation = self.get_object()
        # ... (similar check as accept)
        if not (invitation.email_or_phone == request.user.phone_number or 
                (request.user.email and invitation.email_or_phone == request.user.email)):
            return Response({"error": "This invitation is not for you."}, status=status.HTTP_403_FORBIDDEN)

        if invitation.status != 'pending':
            return Response({'error': 'Invitation already responded to'}, status=status.HTTP_400_BAD_REQUEST)
        
        invitation.status = 'rejected'
        invitation.save()
        return Response({'status': 'invitation rejected'})

@login_required
def kikoba_contribution_config_view(request, kikoba_id):
    kikoba = get_object_or_404(Kikoba, id=kikoba_id)
    # Ensure the user is an admin of this Kikoba (implement your permission logic here)
    # For example, check if the user is the creator or has a specific role
    if not (request.user == kikoba.created_by or request.user.user_kikoba_memberships.filter(kikoba=kikoba, role='kikoba_admin').exists()):
        messages.error(request, "You don't have permission to configure this Kikoba.")
        # Consider redirecting to a more appropriate page, like the dashboard home or kikoba detail page
        return redirect(reverse_lazy('dashboard:kikoba_admin_dashboard', kwargs={'kikoba_id': kikoba.id}))

    config, created = KikobaContributionConfig.objects.get_or_create(kikoba=kikoba)

    if request.method == 'POST':
        form = KikobaContributionConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contribution configuration updated successfully.')
            return redirect(reverse_lazy('groups:kikoba_contribution_config', kwargs={'kikoba_id': kikoba.id}))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = KikobaContributionConfigForm(instance=config)

    context = {
        'form': form,
        'current_kikoba': kikoba,
        'page_title': f'Configure Contributions for {kikoba.name}'
    }
    return render(request, 'groups/kikoba_contribution_config.html', context)

@login_required
def record_entry_fee_payment(request, kikoba_id, member_id):
    kikoba = get_object_or_404(Kikoba, id=kikoba_id)
    # Add permission check: only kikoba admins/treasurer can record payments
    # Example basic permission:
    # if not request.user.user_kikoba_memberships.filter(kikoba=kikoba, role__in=['kikoba_admin', 'treasurer']).exists():
    #     messages.error(request, "You don't have permission to perform this action.")
    #     return redirect(reverse_lazy('dashboard:kikoba_admin_dashboard', kwargs={\'kikoba_id\': kikoba.id}))

    config = getattr(kikoba, 'contribution_config', None)
    if not config:
        messages.error(request, f"Contribution configuration for {kikoba.name} not set up.")
        return redirect(reverse_lazy('dashboard:kikoba_admin_dashboard', kwargs={'kikoba_id': kikoba.id}))

    member = None
    entry_fee_payment = None # Initialize to None

    # Fetch all active members for display
    all_members_status = []
    active_memberships = KikobaMembership.objects.filter(kikoba=kikoba, is_active=True).select_related('user')
    for mem in active_memberships:
        payment_info = EntryFeePayment.objects.filter(kikoba_membership=mem).first()
        status = {
            'member_id': mem.id,
            'name': mem.user.name if hasattr(mem.user, 'name') and mem.user.name else mem.user.username,
            'paid': payment_info.amount_paid if payment_info else 0, # Changed from get_total_paid()
            'due': payment_info.amount_due if payment_info else config.entry_fee_amount,
            'is_fully_paid': payment_info.is_fully_paid if payment_info else False,
            'payment_id': payment_info.id if payment_info else None
        }
        all_members_status.append(status)


    if member_id and member_id != "0": # Check if a specific member is targeted
        member = get_object_or_404(KikobaMembership, id=member_id, kikoba=kikoba)
        entry_fee_payment, created = EntryFeePayment.objects.get_or_create(
            kikoba_membership=member,
            defaults={'amount_due': config.entry_fee_amount if config else 0}
        )
        if not created and config and entry_fee_payment.amount_due != config.entry_fee_amount:
            entry_fee_payment.amount_due = config.entry_fee_amount
            # entry_fee_payment.save() # Decide if this auto-update is desired
    else: # No specific member, or member_id is "0"
        entry_fee_payment = None # Form will be unbound or for a new payment

    if request.method == 'POST':
        # If member was pre-selected (editing existing or creating for specific from URL)
        if member and entry_fee_payment:
            form = EntryFeePaymentForm(request.POST, instance=entry_fee_payment, kikoba=kikoba)
        else: # Creating a new payment, member will be selected in the form
            form = EntryFeePaymentForm(request.POST, kikoba=kikoba)
        
        if form.is_valid():
            payment = form.save(commit=False)
            # If kikoba_membership is not set (e.g. new record where member is selected in form)
            # it should be set by the form. If member was from URL, it's already set on instance.
            if not hasattr(payment, 'kikoba_membership') or not payment.kikoba_membership:
                 payment.kikoba_membership = form.cleaned_data['kikoba_membership']
            
            # Ensure amount_due is set from config if not already set or if it's a new record
            if not payment.amount_due and config:
                payment.amount_due = config.entry_fee_amount
            
            payment.update_payment_status() # Recalculate is_fully_paid
            messages.success(request, f'Entry fee payment for {payment.kikoba_membership.user.name} recorded.')
            return redirect(reverse_lazy('dashboard:kikoba_admin_dashboard', kwargs={'kikoba_id': kikoba.id}))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        if member and entry_fee_payment: # Editing existing or creating for specific member from URL
            form = EntryFeePaymentForm(instance=entry_fee_payment, kikoba=kikoba, initial={'kikoba_membership': member})
        else: # New payment, member to be selected in form
            form = EntryFeePaymentForm(kikoba=kikoba, initial={'amount_due': config.entry_fee_amount if config else 0})

    context = {
        'form': form,
        'current_kikoba': kikoba,
        'member': member, # This will be None if member_id was 0
        'all_members_status': all_members_status, # Add this to context
        'page_title': f'Record Entry Fee for {kikoba.name}' if not member else f'Record Entry Fee for {member.user.name}'
    }
    return render(request, 'groups/record_payment_form.html', context)

@login_required
def record_entry_fee_installment(request, payment_id):
    entry_fee_payment = get_object_or_404(EntryFeePayment, id=payment_id)
    kikoba = entry_fee_payment.kikoba_membership.kikoba
    member = entry_fee_payment.kikoba_membership
    # Add permission check

    if request.method == 'POST':
        form = EntryFeeInstallmentForm(request.POST)
        if form.is_valid():
            installment = form.save(commit=False)
            installment.entry_fee_payment = entry_fee_payment
            installment.save() # This will trigger the update in EntryFeePayment model
            messages.success(request, f'Installment for {member.user.name} recorded.')
            # Redirect to the main payment record or member page
            return redirect(reverse_lazy('groups:record_entry_fee_payment', kwargs={'kikoba_id': kikoba.id, 'member_id': member.id}))
    else:
        form = EntryFeeInstallmentForm(initial={'entry_fee_payment': entry_fee_payment})

    context = {
        'form': form,
        'entry_fee_payment': entry_fee_payment,
        'current_kikoba': kikoba,
        'member': member,
        'page_title': f'Add Installment for {member.user.name}'
    }
    return render(request, 'groups/record_installment_form.html', context) # Generic template


@login_required
def record_share_contribution(request, kikoba_id, member_id):
    kikoba = get_object_or_404(Kikoba, id=kikoba_id)
    # Add permission check
    config = getattr(kikoba, 'contribution_config', None)
    if not config or config.share_amount == 0:
        messages.error(request, f"Share contributions for {kikoba.name} are not configured or amount is zero.")
        return redirect(reverse_lazy('dashboard:kikoba_admin_dashboard', kwargs={'kikoba_id': kikoba.id}))

    member = None
    share_contribution = None
    # Note: Share contributions are periodic. This logic might need to be more sophisticated
    # to select an existing period or create a new one.
    # For now, if member_id is provided, we assume we might be editing the LATEST one or creating new.
    if member_id and member_id != "0":
        member = get_object_or_404(KikobaMembership, id=member_id, kikoba=kikoba)
        # This is a simplification: you'd likely want to select a specific share contribution to edit
        # or provide a way to define the period for a new one.
        # share_contribution = ShareContribution.objects.filter(kikoba_membership=member).order_by('-period_end').first()
    
    if request.method == 'POST':
        form = ShareContributionForm(request.POST, kikoba=kikoba)
        if form.is_valid():
            contribution = form.save(commit=False)
            if not contribution.kikoba_membership:
                contribution.kikoba_membership = form.cleaned_data['kikoba_membership']
            
            # Ensure amount_due is set from config
            if not contribution.amount_due and config:
                contribution.amount_due = config.share_amount
            
            contribution.save()
            messages.success(request, f'Share contribution for {contribution.kikoba_membership.user.name} recorded.')
            return redirect(reverse_lazy('dashboard:kikoba_admin_dashboard', kwargs={'kikoba_id': kikoba.id}))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        initial_data = {'amount_due': config.share_amount}
        if member:
            initial_data['kikoba_membership'] = member
        form = ShareContributionForm(kikoba=kikoba, initial=initial_data)
        # If editing a specific share_contribution, you would pass it as instance=share_contribution

    context = {
        'form': form,
        'current_kikoba': kikoba,
        'member': member,
        'page_title': f'Record Share Contribution for {kikoba.name}'
    }
    return render(request, 'groups/record_payment_form.html', context)

@login_required
def record_share_installment(request, contribution_id):
    share_contribution = get_object_or_404(ShareContribution, id=contribution_id)
    kikoba = share_contribution.kikoba_membership.kikoba
    member = share_contribution.kikoba_membership
    # Add permission check

    if request.method == 'POST':
        form = ShareInstallmentForm(request.POST)
        if form.is_valid():
            installment = form.save(commit=False)
            installment.share_contribution = share_contribution
            installment.save()
            messages.success(request, f'Share installment for {member.user.name} recorded.')
            return redirect(reverse_lazy('groups:record_share_contribution', kwargs={'kikoba_id': kikoba.id, 'member_id': member.id})) # Or a better redirect
    else:
        form = ShareInstallmentForm(initial={'share_contribution': share_contribution})

    context = {
        'form': form,
        'share_contribution': share_contribution,
        'current_kikoba': kikoba,
        'member': member,
        'page_title': f'Add Share Installment for {member.user.name}'
    }
    return render(request, 'groups/record_installment_form.html', context)

@login_required
def record_saving(request, kikoba_id, member_id):
    kikoba = get_object_or_404(Kikoba, id=kikoba_id)
    # Add permission check
    config = getattr(kikoba, 'contribution_config', None)
    member = None
    if member_id and member_id != "0":
        member = get_object_or_404(KikobaMembership, id=member_id, kikoba=kikoba)

    if request.method == 'POST':
        form = SavingForm(request.POST, kikoba=kikoba)
        if form.is_valid():
            saving = form.save(commit=False)
            if not saving.kikoba_membership:
                 saving.kikoba_membership = form.cleaned_data['kikoba_membership']

            # Validate against min/max saving if configured
            if config:
                if config.min_saving_amount and saving.amount < config.min_saving_amount:
                    form.add_error('amount', f'Minimum saving is {config.min_saving_amount}.')
                elif config.max_saving_amount and saving.amount > config.max_saving_amount:
                    form.add_error('amount', f'Maximum saving is {config.max_saving_amount}.')
                
                if not form.errors:
                    saving.save()
                    messages.success(request, f'Saving for {saving.kikoba_membership.user.name} recorded.')
                    return redirect(reverse_lazy('dashboard:kikoba_admin_dashboard', kwargs={'kikoba_id': kikoba.id}))
            else: # No config, just save
                 saving.save()
                 messages.success(request, f'Saving for {saving.kikoba_membership.user.name} recorded.')
                 return redirect(reverse_lazy('dashboard:kikoba_admin_dashboard', kwargs={'kikoba_id': kikoba.id}))
        if form.errors:
             messages.error(request, "Please correct the errors below.")
    else:
        initial_data = {}
        if member:
            initial_data['kikoba_membership'] = member
        form = SavingForm(kikoba=kikoba, initial=initial_data)

    context = {
        'form': form,
        'current_kikoba': kikoba,
        'member': member,
        'page_title': f'Record Saving for {kikoba.name}'
    }
    return render(request, 'groups/record_payment_form.html', context)

@login_required
def record_emergency_fund_contribution(request, kikoba_id, member_id):
    kikoba = get_object_or_404(Kikoba, id=kikoba_id)
    # Add permission check
    config = getattr(kikoba, 'contribution_config', None)
    member = None
    if member_id and member_id != "0":
        member = get_object_or_404(KikobaMembership, id=member_id, kikoba=kikoba)

    # Check if emergency fund is configured
    if not config or config.emergency_fund_amount == 0:
        if not config or not config.emergency_fund_required:
             messages.info(request, f"Emergency fund contributions for {kikoba.name} are not mandatory or amount is zero. You can still record a voluntary contribution.")
        # Allow recording even if not mandatory, but amount might be fixed by config if set

    if request.method == 'POST':
        form = EmergencyFundContributionForm(request.POST, kikoba=kikoba)
        if form.is_valid():
            contribution = form.save(commit=False)
            if not contribution.kikoba_membership:
                contribution.kikoba_membership = form.cleaned_data['kikoba_membership']
            
            # If amount is fixed by config, you might want to enforce it here or in the form
            if config and config.emergency_fund_required and config.emergency_fund_amount > 0 and contribution.amount != config.emergency_fund_amount:
                messages.warning(request, f'The configured emergency fund amount is {config.emergency_fund_amount}, but {contribution.amount} was entered. Since it is required, the amount should match.')
                # form.add_error('amount', f'Required amount is {config.emergency_fund_amount}.') # Uncomment to make it a hard error
            
            if not form.errors:
                contribution.save()
                messages.success(request, f'Emergency fund contribution for {contribution.kikoba_membership.user.name} recorded.')
                return redirect(reverse_lazy('dashboard:kikoba_admin_dashboard', kwargs={'kikoba_id': kikoba.id}))
        if form.errors:
            messages.error(request, "Please correct the errors below.")
    else:
        initial_amount = config.emergency_fund_amount if config and config.emergency_fund_amount > 0 and config.emergency_fund_required else None
        initial_data = {'amount': initial_amount}
        if member:
            initial_data['kikoba_membership'] = member
        form = EmergencyFundContributionForm(kikoba=kikoba, initial=initial_data)

    context = {
        'form': form,
        'current_kikoba': kikoba,
        'member': member,
        'page_title': f'Record Emergency Fund for {kikoba.name}'
    }
    return render(request, 'groups/record_payment_form.html', context)
