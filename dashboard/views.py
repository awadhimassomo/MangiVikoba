from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Q
from .forms import AddMemberForm, AddLoanForm, PolicyLinkForm
from .models import PolicyLink
from registration.models import User 
from loans.models import Loan, LoanApplication
from groups.models import Kikoba, KikobaMembership
from django.contrib.admin.views.decorators import staff_member_required

# Create your views here.

@login_required
def dashboard_home(request):
    user = request.user

    # Check if the user is an admin (chairperson, etc.) of any active Kikoba
    admin_membership = KikobaMembership.objects.filter(
        user=user,
        role__in=['chairperson', 'kikoba_admin', 'treasurer', 'secretary'],
        is_active=True
    ).first()

    if admin_membership:
        return redirect('dashboard:kikoba_admin_dashboard', kikoba_id=admin_membership.kikoba.id)

    # If not an admin, check if they are a member of any active Kikoba
    member_membership = KikobaMembership.objects.filter(
        user=user,
        role='member',
        is_active=True
    ).first()

    if member_membership:
        return redirect('dashboard:member_dashboard')

    # If the user has no active memberships, show a relevant page
    messages.warning(request, "You are not currently a member of any active Kikoba.")
    return render(request, 'dashboard/no_kikoba_assigned.html')

def accountant_check(user):
    return user.role == 'accountant' or user.is_superuser

@login_required
@user_passes_test(accountant_check, login_url='dashboard:home')
def accountant_dashboard(request):
    # Get all pending loan applications
    pending_loans = LoanApplication.objects.filter(status='pending').select_related('member', 'member__user')
    
    # Get loan statistics
    loan_stats = LoanApplication.objects.aggregate(
        total_loans=Count('id'),
        pending_loans=Count('id', filter=Q(status='pending')),
        approved_loans=Count('id', filter=Q(status='approved')),
        rejected_loans=Count('id', filter=Q(status='rejected')),
        total_amount=Sum('amount', filter=Q(status__in=['approved', 'disbursed', 'repaid'])),
    )
    
    # Get recent loan activities
    recent_activities = LoanApplication.objects.order_by('-created_at')[:10]
    
    context = {
        'pending_loans': pending_loans,
        'loan_stats': loan_stats,
        'recent_activities': recent_activities,
    }
    return render(request, 'dashboard/accountant/dashboard.html', context)

@login_required
def kikoba_admin_dashboard(request, kikoba_id=None):
    # Superuser logic: they can see any dashboard by ID, or a list if no ID is provided
    if request.user.is_superuser:
        if kikoba_id:
            current_kikoba = get_object_or_404(Kikoba, id=kikoba_id)
        else:
            # If no ID, show the list of all kikobas for the superuser to choose
            all_kikobas = Kikoba.objects.all()
            context = {
                'page_title': 'Site Administrator Dashboard',
                'all_kikobas': all_kikobas,
                'is_superuser_dashboard': True,
            }
            return render(request, 'dashboard/kikoba_admin_dashboard.html', context)
    else:
        # Regular admin logic: they must be an admin of the requested Kikoba
        admin_membership = get_object_or_404(
            KikobaMembership,
            user=request.user,
            kikoba_id=kikoba_id,
            role__in=['kikoba_admin', 'chairperson', 'treasurer', 'secretary'],
            is_active=True
        )
        current_kikoba = admin_membership.kikoba
    
    # Fetch data for the dashboard
    total_members = KikobaMembership.objects.filter(kikoba=current_kikoba, is_active=True).count()
    total_loans = Loan.objects.filter(application__kikoba=current_kikoba).count()

    context = {
        'page_title': f'Admin Dashboard - {current_kikoba.name}',
        'current_kikoba': current_kikoba,
        'total_members': total_members,
        'total_loans': total_loans,
        'total_savings': '1,250,000 TZS', # Placeholder
    }

    return render(request, 'dashboard/kikoba_admin_dashboard.html', context)


@login_required
def member_dashboard(request):
    user = request.user
    memberships = KikobaMembership.objects.filter(
        user=user, 
        role='member', 
        is_active=True
    ).select_related('kikoba')

    if not memberships.exists():
        messages.warning(request, "You are not currently an active member of any Kikoba.")
        return render(request, 'dashboard/no_kikoba_assigned.html')
    
    kikoba_id_to_view = request.GET.get('kikoba_id')
    current_kikoba_membership = None

    if kikoba_id_to_view:
        current_kikoba_membership = memberships.filter(kikoba_id=kikoba_id_to_view).first()
    
    if not current_kikoba_membership and memberships.exists():
        current_kikoba_membership = memberships.first()

    context = {
        'page_title': 'Member Dashboard',
        'memberships': memberships,
        'current_kikoba_membership': current_kikoba_membership,
    }
    return render(request, 'dashboard/member_dashboard.html', context)

# --- Other views ---

@login_required
def loan_management(request):
    """
    Loan management page showing all loans and applications for user's kikoba(s).
    """
    user = request.user
    
    # Check if user is an admin of any kikoba
    admin_membership = KikobaMembership.objects.filter(
        user=user,
        role__in=['chairperson', 'kikoba_admin', 'treasurer', 'secretary', 'accountant'],
        is_active=True
    ).select_related('kikoba').first()
    
    if admin_membership:
        # User is an admin - show their kikoba's loans
        current_kikoba = admin_membership.kikoba
        
        # Get loan applications by status
        pending_applications = LoanApplication.objects.filter(
            kikoba=current_kikoba,
            status='pending'
        ).select_related('member', 'loan_product').order_by('-application_date')
        
        approved_applications = LoanApplication.objects.filter(
            kikoba=current_kikoba,
            status='approved'
        ).select_related('member', 'loan_product', 'decision_by').order_by('-decision_date')
        
        rejected_applications = LoanApplication.objects.filter(
            kikoba=current_kikoba,
            status='rejected'
        ).select_related('member', 'loan_product', 'decision_by').order_by('-decision_date')
        
        # Get active loans
        active_loans = Loan.objects.filter(
            application__kikoba=current_kikoba,
            status='active'
        ).select_related('application__member', 'application__loan_product').order_by('-disbursement_date')
        
        # Get loan statistics
        from django.db.models import Sum
        total_disbursed = Loan.objects.filter(
            application__kikoba=current_kikoba,
            status__in=['active', 'paid_on_time']
        ).aggregate(total=Sum('disbursed_amount'))['total'] or 0
        
        total_repayable = Loan.objects.filter(
            application__kikoba=current_kikoba,
            status='active'
        ).aggregate(total=Sum('total_repayable'))['total'] or 0
        
        context = {
            'page_title': f'Loan Management - {current_kikoba.name}',
            'current_kikoba': current_kikoba,
            'pending_applications': pending_applications,
            'approved_applications': approved_applications,
            'rejected_applications': rejected_applications,
            'active_loans': active_loans,
            'is_admin': True,
            'total_pending': pending_applications.count(),
            'total_approved': approved_applications.count(),
            'total_rejected': rejected_applications.count(),
            'total_active_loans': active_loans.count(),
            'total_disbursed': total_disbursed,
            'total_repayable': total_repayable,
        }
    else:
        # User is a regular member - show their own loan applications and loans
        member_applications = LoanApplication.objects.filter(
            member=user
        ).select_related('kikoba', 'loan_product', 'decision_by').order_by('-application_date')
        
        member_loans = Loan.objects.filter(
            application__member=user
        ).select_related('application__kikoba', 'application__loan_product').order_by('-disbursement_date')
        
        context = {
            'page_title': 'My Loans',
            'member_applications': member_applications,
            'member_loans': member_loans,
            'is_admin': False,
        }
    
    return render(request, 'dashboard/loan_management.html', context)

@login_required
def member_management(request):
    context = {'page_title': 'Member Management'}
    return render(request, 'dashboard/member_management.html', context)

@login_required
def entry_fee_management(request):
    # Get user's admin membership
    admin_membership = KikobaMembership.objects.filter(
        user=request.user,
        role__in=['kikoba_admin', 'chairperson', 'treasurer', 'secretary'],
        is_active=True
    ).select_related('kikoba').first()
    
    print(f"DEBUG: User = {request.user}")
    print(f"DEBUG: Admin membership = {admin_membership}")
    
    if not admin_membership:
        messages.error(request, "You do not have access to entry fee management.")
        return redirect('dashboard:home')
    
    current_kikoba = admin_membership.kikoba
    print(f"DEBUG: Current Kikoba = {current_kikoba}")
    
    # Import the EntryFeePayment model
    from groups.models import EntryFeePayment
    from django.utils import timezone
    
    # Handle POST request (recording new payment)
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        payment_note = request.POST.get('payment_note', '')
        
        if not member_id:
            messages.error(request, "Please select a member to record payment.")
            return redirect('dashboard:entry_fee_management')
        
        try:
            # Get the member
            member = KikobaMembership.objects.get(
                id=member_id,
                kikoba=current_kikoba,
                is_active=True
            )
            
            # Get entry fee amount from config
            entry_fee_amount = current_kikoba.contribution_config.entry_fee_amount if hasattr(current_kikoba, 'contribution_config') else 0
            
            # Get or create entry fee payment record
            entry_fee_payment, created = EntryFeePayment.objects.get_or_create(
                kikoba_membership=member,
                defaults={
                    'amount_due': entry_fee_amount,
                    'amount_paid': entry_fee_amount,
                    'payment_date': timezone.now(),
                    'payment_method': 'cash',
                    'is_fully_paid': True,
                    'notes': payment_note,
                }
            )
            
            if not created:
                # Update existing payment
                entry_fee_payment.is_fully_paid = True
                entry_fee_payment.amount_paid = entry_fee_amount
                entry_fee_payment.amount_due = entry_fee_amount
                entry_fee_payment.payment_date = timezone.now()
                entry_fee_payment.notes = payment_note
                entry_fee_payment.save()
            
            messages.success(request, f"✅ Entry fee payment recorded for {member.user.name}")
            return redirect('dashboard:entry_fee_management')
            
        except KikobaMembership.DoesNotExist:
            messages.error(request, "Selected member not found.")
            return redirect('dashboard:entry_fee_management')
        except Exception as e:
            messages.error(request, f"Error recording payment: {str(e)}")
            return redirect('dashboard:entry_fee_management')
    
    # Get ALL active members regardless of role (includes chairpersons, treasurers, etc.)
    members = KikobaMembership.objects.filter(
        kikoba=current_kikoba,
        is_active=True
    ).select_related('user')
    
    print(f"DEBUG: Members count = {members.count()}")
    print(f"DEBUG: Members = {list(members.values('id', 'user__name', 'role', 'is_active'))}")
    
    # Import the EntryFeePayment model to check payment status
    from groups.models import EntryFeePayment
    
    # Build members_payment_status list for the template
    members_payment_status = []
    paid_members_ids = []
    
    for member in members:
        # Check if this member has an entry fee payment record
        entry_fee_payment = EntryFeePayment.objects.filter(
            kikoba_membership=member
        ).first()
        
        if entry_fee_payment and entry_fee_payment.is_fully_paid:
            has_paid = True
            paid_members_ids.append(member.id)
            payment_details = {
                'amount_paid': entry_fee_payment.amount_paid,
                'payment_date': entry_fee_payment.payment_date,
                'payment_method': entry_fee_payment.payment_method,
            }
        else:
            has_paid = False
            payment_details = None
        
        members_payment_status.append({
            'member': member,
            'has_paid': has_paid,
            'payment_details': payment_details,
        })
    
    context = {
        'page_title': f'Entry Fee Management - {current_kikoba.name}',
        'group': current_kikoba,
        'group_members': members,  # Template expects 'group_members'
        'paid_members_ids': paid_members_ids,
        'members_payment_status': members_payment_status,  # Add the missing variable
    }
    return render(request, 'dashboard/entry_fee_management.html', context)

@login_required
def share_contributions_management(request):
    """
    Share contributions management page showing all members and their total contributions.
    """
    # Get user's admin membership
    admin_membership = KikobaMembership.objects.filter(
        user=request.user,
        role__in=['kikoba_admin', 'chairperson', 'treasurer', 'secretary'],
        is_active=True
    ).select_related('kikoba').first()
    
    if not admin_membership:
        messages.error(request, "You do not have access to share contributions management.")
        return redirect('dashboard:home')
    
    current_kikoba = admin_membership.kikoba
    
    # Import required models
    from groups.models import ShareContribution, ShareInstallment
    from django.db.models import Sum, Count
    
    # Handle POST request (recording new contribution)
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        period_start = request.POST.get('period_start')
        period_end = request.POST.get('period_end')
        amount_paid = request.POST.get('amount_paid', 0)
        
        if not member_id:
            messages.error(request, "Please select a member to record contribution.")
            return redirect('dashboard:share_contributions_management')
        
        try:
            # Get the member
            member = KikobaMembership.objects.get(
                id=member_id,
                kikoba=current_kikoba,
                is_active=True
            )
            
            # Get share amount from config
            share_amount = current_kikoba.contribution_config.share_amount if hasattr(current_kikoba, 'contribution_config') else 0
            
            # Create share contribution record
            share_contribution = ShareContribution.objects.create(
                kikoba_membership=member,
                amount_due=share_amount,
                amount_paid=float(amount_paid) if amount_paid else 0,
                is_fully_paid=(float(amount_paid) >= float(share_amount)) if amount_paid and share_amount else False,
                period_start=period_start if period_start else timezone.now().date(),
                period_end=period_end if period_end else timezone.now().date(),
            )
            
            messages.success(request, f"✅ Share contribution recorded for {member.user.name}")
            return redirect('dashboard:share_contributions_management')
            
        except KikobaMembership.DoesNotExist:
            messages.error(request, "Selected member not found.")
            return redirect('dashboard:share_contributions_management')
        except Exception as e:
            messages.error(request, f"Error recording contribution: {str(e)}")
            return redirect('dashboard:share_contributions_management')
    
    # Get ALL active members
    members = KikobaMembership.objects.filter(
        kikoba=current_kikoba,
        is_active=True
    ).select_related('user')
    
    # Build members_contributions_status list for the template
    members_contributions_status = []
    
    for member in members:
        # Get all share contributions for this member
        contributions = ShareContribution.objects.filter(
            kikoba_membership=member
        ).order_by('-period_end')
        
        # Calculate total contributions
        total_paid = contributions.aggregate(total=Sum('amount_paid'))['total'] or 0
        total_due = contributions.aggregate(total=Sum('amount_due'))['total'] or 0
        contribution_count = contributions.count()
        
        # Get recent contributions (last 3)
        recent_contributions = list(contributions[:3])
        
        members_contributions_status.append({
            'member': member,
            'total_paid': total_paid,
            'total_due': total_due,
            'contribution_count': contribution_count,
            'recent_contributions': recent_contributions,
            'all_contributions': contributions,
        })
    
    # Get share amount from config
    share_amount = current_kikoba.contribution_config.share_amount if hasattr(current_kikoba, 'contribution_config') else 0
    
    context = {
        'page_title': f'Share Contributions Management - {current_kikoba.name}',
        'group': current_kikoba,
        'group_members': members,
        'members_contributions_status': members_contributions_status,
        'share_amount': share_amount,
    }
    return render(request, 'dashboard/share_contributions_management.html', context)

@login_required
def savings_management(request):
    """
    Savings management page showing all members and their total savings contributions.
    """
    # Get user's admin membership
    admin_membership = KikobaMembership.objects.filter(
        user=request.user,
        role__in=['kikoba_admin', 'chairperson', 'treasurer', 'secretary'],
        is_active=True
    ).select_related('kikoba').first()
    
    if not admin_membership:
        messages.error(request, "You do not have access to savings management.")
        return redirect('dashboard:home')
    
    current_kikoba = admin_membership.kikoba
    
    # Import required models
    from groups.models import Saving
    from django.db.models import Sum, Count
    
    # Handle POST request (recording new saving)
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        amount = request.POST.get('amount', 0)
        saved_on = request.POST.get('saved_on')
        
        if not member_id:
            messages.error(request, "Please select a member to record saving.")
            return redirect('dashboard:savings_management')
        
        try:
            # Get the member
            member = KikobaMembership.objects.get(
                id=member_id,
                kikoba=current_kikoba,
                is_active=True
            )
            
            # Create saving record
            saving = Saving.objects.create(
                kikoba_membership=member,
                amount=float(amount) if amount else 0,
            )
            
            # Update saved_on if provided (otherwise auto_now_add handles it)
            if saved_on:
                saving.saved_on = saved_on
                saving.save()
            
            messages.success(request, f"✅ Saving recorded for {member.user.name}")
            return redirect('dashboard:savings_management')
            
        except KikobaMembership.DoesNotExist:
            messages.error(request, "Selected member not found.")
            return redirect('dashboard:savings_management')
        except Exception as e:
            messages.error(request, f"Error recording saving: {str(e)}")
            return redirect('dashboard:savings_management')
    
    # Get ALL active members
    members = KikobaMembership.objects.filter(
        kikoba=current_kikoba,
        is_active=True
    ).select_related('user')
    
    # Build members_savings_status list for the template
    members_savings_status = []
    
    for member in members:
        # Get all savings for this member
        savings = Saving.objects.filter(
            kikoba_membership=member
        ).order_by('-saved_on')
        
        # Calculate total savings
        total_saved = savings.aggregate(total=Sum('amount'))['total'] or 0
        savings_count = savings.count()
        
        # Get recent savings (last 5)
        recent_savings = list(savings[:5])
        
        members_savings_status.append({
            'member': member,
            'total_saved': total_saved,
            'savings_count': savings_count,
            'recent_savings': recent_savings,
            'all_savings': savings,
        })
    
    # Get min/max saving amounts from config if available
    min_saving = current_kikoba.contribution_config.min_saving_amount if hasattr(current_kikoba, 'contribution_config') else None
    max_saving = current_kikoba.contribution_config.max_saving_amount if hasattr(current_kikoba, 'contribution_config') else None
    
    context = {
        'page_title': f'Savings Management - {current_kikoba.name}',
        'group': current_kikoba,
        'group_members': members,
        'members_savings_status': members_savings_status,
        'min_saving': min_saving,
        'max_saving': max_saving,
    }
    return render(request, 'dashboard/savings_management.html', context)

@login_required
def emergency_fund_management(request):
    """
    Emergency fund management page showing all members and their total emergency fund contributions.
    """
    # Get user's admin membership
    admin_membership = KikobaMembership.objects.filter(
        user=request.user,
        role__in=['kikoba_admin', 'chairperson', 'treasurer', 'secretary'],
        is_active=True
    ).select_related('kikoba').first()
    
    if not admin_membership:
        messages.error(request, "You do not have access to emergency fund management.")
        return redirect('dashboard:home')
    
    current_kikoba = admin_membership.kikoba
    
    # Import required models
    from groups.models import EmergencyFundContribution
    from django.db.models import Sum, Count
    
    # Handle POST request (recording new contribution)
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        amount = request.POST.get('amount', 0)
        contributed_on = request.POST.get('contributed_on')
        
        if not member_id:
            messages.error(request, "Please select a member to record contribution.")
            return redirect('dashboard:emergency_fund_management')
        
        try:
            # Get the member
            member = KikobaMembership.objects.get(
                id=member_id,
                kikoba=current_kikoba,
                is_active=True
            )
            
            # Create emergency fund contribution record
            contribution = EmergencyFundContribution.objects.create(
                kikoba_membership=member,
                amount=float(amount) if amount else 0,
            )
            
            # Update contributed_on if provided (otherwise auto_now_add handles it)
            if contributed_on:
                contribution.contributed_on = contributed_on
                contribution.save()
            
            messages.success(request, f"✅ Emergency fund contribution recorded for {member.user.name}")
            return redirect('dashboard:emergency_fund_management')
            
        except KikobaMembership.DoesNotExist:
            messages.error(request, "Selected member not found.")
            return redirect('dashboard:emergency_fund_management')
        except Exception as e:
            messages.error(request, f"Error recording contribution: {str(e)}")
            return redirect('dashboard:emergency_fund_management')
    
    # Get ALL active members
    members = KikobaMembership.objects.filter(
        kikoba=current_kikoba,
        is_active=True
    ).select_related('user')
    
    # Build members_emergency_fund_status list for the template
    members_emergency_fund_status = []
    
    for member in members:
        # Get all emergency fund contributions for this member
        contributions = EmergencyFundContribution.objects.filter(
            kikoba_membership=member
        ).order_by('-contributed_on')
        
        # Calculate total contributions
        total_contributed = contributions.aggregate(total=Sum('amount'))['total'] or 0
        contributions_count = contributions.count()
        
        # Get recent contributions (last 5)
        recent_contributions = list(contributions[:5])
        
        members_emergency_fund_status.append({
            'member': member,
            'total_contributed': total_contributed,
            'contributions_count': contributions_count,
            'recent_contributions': recent_contributions,
            'all_contributions': contributions,
        })
    
    # Get emergency fund amount from config if available
    emergency_fund_amount = current_kikoba.contribution_config.emergency_fund_amount if hasattr(current_kikoba, 'contribution_config') else None
    emergency_fund_required = current_kikoba.contribution_config.emergency_fund_required if hasattr(current_kikoba, 'contribution_config') else False
    
    context = {
        'page_title': f'Emergency Fund Management - {current_kikoba.name}',
        'group': current_kikoba,
        'group_members': members,
        'members_emergency_fund_status': members_emergency_fund_status,
        'emergency_fund_amount': emergency_fund_amount,
        'emergency_fund_required': emergency_fund_required,
    }
    return render(request, 'dashboard/emergency_fund_management.html', context)

@login_required
def interest_management(request):
    context = {'page_title': 'Interest Management'}
    return render(request, 'dashboard/interest_management.html', context)

@login_required
def policy_management(request):
    admin_membership = KikobaMembership.objects.filter(user=request.user, role__in=['kikoba_admin', 'chairperson', 'treasurer'], is_active=True).select_related('kikoba').first()
    if not admin_membership:
        messages.error(request, "You do not have administrative access for policy management.")
        return redirect('dashboard:home')
    current_kikoba = admin_membership.kikoba
    if request.method == 'POST':
        form = PolicyLinkForm(request.POST)
        if form.is_valid():
            policy_link = form.save(commit=False)
            policy_link.kikoba = current_kikoba
            policy_link.added_by = request.user
            policy_link.save()
            messages.success(request, "Policy link added successfully.")
            return redirect('dashboard:policy_management')
    else:
        form = PolicyLinkForm()
    policy_links = PolicyLink.objects.filter(kikoba=current_kikoba)
    context = {
        'page_title': f'Policy Management - {current_kikoba.name}',
        'current_kikoba': current_kikoba,
        'form': form,
        'policy_links': policy_links,
    }
    return render(request, 'dashboard/policy_management.html', context)

@login_required
def settings_view(request):
    context = {'page_title': 'Application Settings'}
    return render(request, 'dashboard/settings.html', context)

@login_required
def profile_view(request):
    context = {'page_title': 'User Profile'}
    return render(request, 'dashboard/profile.html', context)

@login_required
def emergency_funds_view(request):
    context = {'page_title': 'Emergency Funds'}
    return render(request, 'dashboard/emergency_funds.html', context)

@login_required
def add_member_view(request):
    # This view logic needs to be associated with a specific Kikoba
    # For now, it's a generic add member form
    if request.method == 'POST':
        form = AddMemberForm(request.POST)
        if form.is_valid():
            try:
                User.objects.create_user(
                    phone_number=form.cleaned_data['phone_number'],
                    name=form.cleaned_data['name'],
                    password=form.cleaned_data['password']
                )
                messages.success(request, 'Member added successfully!')
                return redirect('dashboard:member_management')
            except Exception as e:
                messages.error(request, f'Error adding member: {e}')
    else:
        form = AddMemberForm()
    context = {
        'page_title': 'Add New Member',
        'form': form
    }
    return render(request, 'dashboard/add_member.html', context)

@login_required
def add_loan_view(request):
    # This view logic needs to be associated with a specific Kikoba
    # For now, it's a generic add loan form
    admin_membership = KikobaMembership.objects.filter(user=request.user, role__in=['kikoba_admin', 'chairperson', 'treasurer'], is_active=True).first()
    if not admin_membership:
        messages.error(request, "You do not have admin rights to add loans.")
        return redirect('dashboard:loan_management')
    
    admin_kikoba = admin_membership.kikoba
    if request.method == 'POST':
        form = AddLoanForm(request.POST, admin_kikoba=admin_kikoba)
        if form.is_valid():
            try:
                loan = form.save(commit=False)
                loan.kikoba = admin_kikoba
                loan.approved_by = request.user
                loan.status = 'pending'
                loan.save()
                messages.success(request, 'Loan application submitted successfully!')
                return redirect('dashboard:loan_management')
            except Exception as e:
                messages.error(request, f'Error submitting loan application: {e}')
    else:
        form = AddLoanForm(admin_kikoba=admin_kikoba)
    context = {
        'form': form,
        'page_title': f'Add New Loan for {admin_kikoba.name}',
    }
    return render(request, 'dashboard/add_loan.html', context)

# Restrict Django admin to superusers only
from django.contrib import admin

@login_required
def group_management_view(request):
    admin_membership = KikobaMembership.objects.filter(user=request.user, role__in=['kikoba_admin', 'chairperson', 'treasurer'], is_active=True).select_related('kikoba').first()
    if not admin_membership:
        messages.error(request, "You do not have administrative access to manage groups.")
        return redirect('dashboard:home')
    current_kikoba = admin_membership.kikoba
    members = KikobaMembership.objects.filter(kikoba=current_kikoba, is_active=True).select_related('user')
    context = {
        'page_title': 'Group Management',
        'current_kikoba': current_kikoba,
        'members': members,
    }
    return render(request, 'dashboard/group_management.html', context)

@login_required
def savings_contributions_view(request):
    admin_membership = KikobaMembership.objects.filter(user=request.user, role__in=['kikoba_admin', 'chairperson', 'treasurer'], is_active=True).select_related('kikoba').first()
    if not admin_membership:
        messages.error(request, "You do not have administrative access.")
        return redirect('dashboard:home')
    current_kikoba = admin_membership.kikoba
    members = KikobaMembership.objects.filter(kikoba=current_kikoba, is_active=True).select_related('user')
    context = {
        'page_title': f'Savings & Contributions - {current_kikoba.name}',
        'current_kikoba': current_kikoba,
        'members': members,
    }
    return render(request, 'dashboard/savings_contributions.html', context)

@login_required
def credit_score_engine_view(request):
    admin_membership = KikobaMembership.objects.filter(user=request.user, role__in=['kikoba_admin', 'chairperson', 'treasurer'], is_active=True).select_related('kikoba').first()
    if not admin_membership:
        messages.error(request, "You do not have administrative access.")
        return redirect('dashboard:home')
    current_kikoba = admin_membership.kikoba
    context = {
        'page_title': f'Shared Credit Score Engine - {current_kikoba.name}',
        'current_kikoba': current_kikoba,
    }
    return render(request, 'dashboard/credit_score_engine.html', context)

@login_required
def auditing_reporting_view(request):
    admin_membership = KikobaMembership.objects.filter(user=request.user, role__in=['kikoba_admin', 'chairperson', 'treasurer'], is_active=True).select_related('kikoba').first()
    if not admin_membership:
        messages.error(request, "You do not have administrative access.")
        return redirect('dashboard:home')
    current_kikoba = admin_membership.kikoba
    context = {
        'page_title': f'Auditing & Reporting - {current_kikoba.name}',
        'current_kikoba': current_kikoba,
    }
    return render(request, 'dashboard/auditing_reporting.html', context)

@login_required
def learning_hub_view(request):
    admin_membership = KikobaMembership.objects.filter(user=request.user, role__in=['kikoba_admin', 'chairperson', 'treasurer'], is_active=True).select_related('kikoba').first()
    if not admin_membership:
        messages.error(request, "You do not have administrative access.")
        return redirect('dashboard:home')
    current_kikoba = admin_membership.kikoba
    context = {
        'page_title': f'Learning Hub - {current_kikoba.name}',
        'current_kikoba': current_kikoba,
    }
    return render(request, 'dashboard/learning_hub.html', context)

@login_required
def kikoba_loans_management_view(request):
    admin_membership = KikobaMembership.objects.filter(
        user=request.user, 
        role__in=['kikoba_admin', 'chairperson', 'treasurer', 'accountant'], 
        is_active=True
    ).select_related('kikoba').first()
    if not admin_membership:
        messages.error(request, "You do not have access to loan management.")
        return redirect('dashboard:home')
    current_kikoba = admin_membership.kikoba
    
    # Get loan applications by status
    pending_applications = LoanApplication.objects.filter(
        kikoba=current_kikoba,
        status='pending'
    ).select_related('member', 'loan_product').order_by('-application_date')
    
    approved_applications = LoanApplication.objects.filter(
        kikoba=current_kikoba,
        status='approved'
    ).select_related('member', 'loan_product', 'decision_by').order_by('-decision_date')
    
    rejected_applications = LoanApplication.objects.filter(
        kikoba=current_kikoba,
        status='rejected'
    ).select_related('member', 'loan_product', 'decision_by').order_by('-decision_date')
    
    # Get active loans count
    active_loans_count = Loan.objects.filter(
        application__kikoba=current_kikoba,
        status='active'
    ).count()
    
    context = {
        'page_title': f'Loans Management - {current_kikoba.name}',
        'current_kikoba': current_kikoba,
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'rejected_applications': rejected_applications,
        'active_loans_count': active_loans_count,
        'total_pending': pending_applications.count(),
        'total_approved': approved_applications.count(),
    }
    return render(request, 'dashboard/kikoba_loans_management.html', context)

def record_entry_fee_payment(request, kikoba_id, member_id):
    kikoba = get_object_or_404(Kikoba, id=kikoba_id)
    members = kikoba.groupmember_set.all()
    paid_members = members.filter(entry_fee_paid=True)
    return render(request, 'dashboard/entry_fee_management.html', {
        'group': kikoba,
        'members': members,
        'entry_fee_paid_members': paid_members,
    })

@login_required
def loan_application_detail_view(request, application_id):
    """
    View detailed loan application form for approval/rejection by managers/accountants.
    """
    # Get the loan application
    application = get_object_or_404(LoanApplication, id=application_id)
    
    # Check if user has permission to view this application
    # Must be admin/chairperson/treasurer/accountant of the kikoba
    admin_membership = KikobaMembership.objects.filter(
        user=request.user,
        kikoba=application.kikoba,
        role__in=['kikoba_admin', 'chairperson', 'treasurer', 'accountant'],
        is_active=True
    ).first()
    
    if not admin_membership and not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this loan application.")
        return redirect('dashboard:home')
    
    context = {
        'page_title': f'Loan Application - {application.member.name}',
        'application': application,
        'current_kikoba': application.kikoba,
    }
    return render(request, 'dashboard/loan_application_detail.html', context)

@login_required
def approve_loan_application(request, application_id):
    """
    Approve a loan application.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('dashboard:home')
    
    # Get the loan application
    application = get_object_or_404(LoanApplication, id=application_id)
    
    # Check if user has permission to approve
    admin_membership = KikobaMembership.objects.filter(
        user=request.user,
        kikoba=application.kikoba,
        role__in=['kikoba_admin', 'chairperson', 'treasurer', 'accountant'],
        is_active=True
    ).first()
    
    if not admin_membership and not request.user.is_superuser:
        messages.error(request, "You do not have permission to approve this loan application.")
        return redirect('dashboard:home')
    
    # Check if application is still pending
    if application.status != 'pending':
        messages.warning(request, f"This application has already been {application.status}.")
        return redirect('dashboard:loan_application_detail', application_id=application.id)
    
    # Approve the application
    application.status = 'approved'
    application.decision_by = request.user
    application.decision_date = timezone.now()
    application.remarks = request.POST.get('remarks', '')
    application.save()
    
    messages.success(request, f"Loan application for {application.member.name} has been approved successfully!")
    return redirect('dashboard:loan_application_detail', application_id=application.id)

@login_required
def reject_loan_application(request, application_id):
    """
    Reject a loan application.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('dashboard:home')
    
    # Get the loan application
    application = get_object_or_404(LoanApplication, id=application_id)
    
    # Check if user has permission to reject
    admin_membership = KikobaMembership.objects.filter(
        user=request.user,
        kikoba=application.kikoba,
        role__in=['kikoba_admin', 'chairperson', 'treasurer', 'accountant'],
        is_active=True
    ).first()
    
    if not admin_membership and not request.user.is_superuser:
        messages.error(request, "You do not have permission to reject this loan application.")
        return redirect('dashboard:home')
    
    # Check if application is still pending
    if application.status != 'pending':
        messages.warning(request, f"This application has already been {application.status}.")
        return redirect('dashboard:loan_application_detail', application_id=application.id)
    
    # Get rejection reason (required)
    remarks = request.POST.get('remarks', '').strip()
    if not remarks:
        messages.error(request, "Please provide a reason for rejection.")
        return redirect('dashboard:loan_application_detail', application_id=application.id)
    
    # Reject the application
    application.status = 'rejected'
    application.decision_by = request.user
    application.decision_date = timezone.now()
    application.remarks = remarks
    application.save()
    
    messages.success(request, f"Loan application for {application.member.name} has been rejected.")
    return redirect('dashboard:loan_application_detail', application_id=application.id)