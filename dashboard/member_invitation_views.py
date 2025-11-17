from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from groups.models import KikobaMembership, KikobaInvitation
from sms.utils import send_sms


@login_required
def invite_member_view(request):
    """Admin view to invite new members by phone number"""
    # Get user's admin membership
    admin_membership = KikobaMembership.objects.filter(
        user=request.user,
        role__in=['kikoba_admin', 'chairperson', 'treasurer', 'secretary'],
        is_active=True
    ).select_related('kikoba').first()
    
    if not admin_membership:
        messages.error(request, "You do not have permission to invite members.")
        return redirect('dashboard:home')
    
    current_kikoba = admin_membership.kikoba
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        role = request.POST.get('role', 'member')
        
        if not phone_number:
            messages.error(request, "Please enter a phone number.")
            return redirect('dashboard:invite_member')
        
        # Validate phone number format (basic validation)
        if not phone_number.startswith('+') and not phone_number.startswith('0'):
            messages.error(request, "Phone number should start with + or 0")
            return redirect('dashboard:invite_member')
        
        # Check if invitation already exists for this phone and kikoba
        existing_invitation = KikobaInvitation.objects.filter(
            kikoba=current_kikoba,
            email_or_phone=phone_number,
            status='pending'
        ).first()
        
        if existing_invitation:
            messages.warning(
                request,
                f"An invitation already exists for {phone_number} with code: {existing_invitation.invitation_code}"
            )
            return redirect('dashboard:invite_member')
        
        # Check if member is already in the kikoba
        if KikobaMembership.objects.filter(
            kikoba=current_kikoba,
            user__phone_number=phone_number
        ).exists():
            messages.error(request, f"{phone_number} is already a member of {current_kikoba.name}")
            return redirect('dashboard:invite_member')
        
        try:
            # Create invitation
            invitation = KikobaInvitation.objects.create(
                kikoba=current_kikoba,
                invited_by=request.user,
                email_or_phone=phone_number,
                role=role
            )
            
            # The invitation_code is auto-generated in the model's save() method
            
            # Send SMS with Kikoba number (for registration)
            sms_message = f"Hongera! Umealikwa kujiunga na {current_kikoba.name} Kikoba! Namba ya Kikoba ni: {current_kikoba.kikoba_number}. Jisajili kwenye: http://www.mangivikoba.co.tz/api/auth/register/ (Utakubaliwa moja kwa moja)"
            
            try:
                send_sms(phone_number, sms_message)
                messages.success(
                    request,
                    f"✅ Invitation sent successfully!\n"
                    f"Phone: {phone_number}\n"
                    f"Kikoba Number: {current_kikoba.kikoba_number}\n"
                    f"Invitation Code (for tracking): {invitation.invitation_code}\n"
                    f"SMS has been sent. Member will be auto-approved upon registration."
                )
            except Exception as e:
                messages.warning(
                    request,
                    f"⚠️ Invitation created but SMS failed to send.\n"
                    f"Phone: {phone_number}\n"
                    f"Code: {invitation.invitation_code}\n"
                    f"Please share the code manually. Error: {str(e)}"
                )
            
            return redirect('dashboard:invite_member')
            
        except Exception as e:
            messages.error(request, f"Error creating invitation: {str(e)}")
            return redirect('dashboard:invite_member')
    
    # Get pending invitations for this kikoba
    pending_invitations = KikobaInvitation.objects.filter(
        kikoba=current_kikoba,
        status='pending'
    ).select_related('invited_by').order_by('-created_at')[:20]
    
    # Get accepted invitations (recently joined members)
    accepted_invitations = KikobaInvitation.objects.filter(
        kikoba=current_kikoba,
        status='accepted'
    ).select_related('invited_by').order_by('-updated_at')[:10]
    
    context = {
        'page_title': f'Invite Members - {current_kikoba.name}',
        'current_kikoba': current_kikoba,
        'pending_invitations': pending_invitations,
        'accepted_invitations': accepted_invitations,
    }
    
    return render(request, 'dashboard/invite_member.html', context)


@login_required
def resend_invitation_view(request, invitation_id):
    """Resend invitation SMS"""
    admin_membership = KikobaMembership.objects.filter(
        user=request.user,
        role__in=['kikoba_admin', 'chairperson', 'treasurer', 'secretary'],
        is_active=True
    ).select_related('kikoba').first()
    
    if not admin_membership:
        messages.error(request, "You do not have permission.")
        return redirect('dashboard:home')
    
    try:
        invitation = KikobaInvitation.objects.get(
            id=invitation_id,
            kikoba=admin_membership.kikoba,
            status='pending'
        )
        
        # Resend SMS with Kikoba number
        sms_message = f"Hongera! Umealikwa kujiunga na {invitation.kikoba.name} Kikoba! Namba ya Kikoba ni: {invitation.kikoba.kikoba_number}. Jisajili kwenye: http://www.mangivikoba.co.tz/api/auth/register/ (Utakubaliwa moja kwa moja)"
        
        try:
            send_sms(invitation.email_or_phone, sms_message)
            messages.success(
                request,
                f"✅ Invitation SMS resent successfully!\n"
                f"Code: {invitation.invitation_code}\n"
                f"Phone: {invitation.email_or_phone}"
            )
        except Exception as e:
            messages.warning(
                request,
                f"⚠️ Failed to resend SMS.\n"
                f"Code: {invitation.invitation_code}\n"
                f"Phone: {invitation.email_or_phone}\n"
                f"Error: {str(e)}"
            )
        
    except KikobaInvitation.DoesNotExist:
        messages.error(request, "Invitation not found.")
    
    return redirect('dashboard:invite_member')


@login_required
def cancel_invitation_view(request, invitation_id):
    """Cancel a pending invitation"""
    admin_membership = KikobaMembership.objects.filter(
        user=request.user,
        role__in=['kikoba_admin', 'chairperson', 'treasurer', 'secretary'],
        is_active=True
    ).select_related('kikoba').first()
    
    if not admin_membership:
        messages.error(request, "You do not have permission.")
        return redirect('dashboard:home')
    
    try:
        invitation = KikobaInvitation.objects.get(
            id=invitation_id,
            kikoba=admin_membership.kikoba,
            status='pending'
        )
        
        invitation.status = 'rejected'
        invitation.save()
        
        messages.success(request, f"Invitation for {invitation.email_or_phone} has been cancelled.")
        
    except KikobaInvitation.DoesNotExist:
        messages.error(request, "Invitation not found.")
    
    return redirect('dashboard:invite_member')
