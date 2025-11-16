from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from datetime import timedelta

from .admin_models import (
    Investment, InvestmentParticipation, SystemConfiguration,
    SystemNotification, AuditLog
)
from groups.models import Kikoba, KikobaMembership
from registration.models import User
from loans.models import Loan


def is_superuser(user):
    """Check if user is a superuser"""
    return user.is_superuser


def log_admin_action(user, action, model_name, object_id, description, request):
    """Helper function to log admin actions"""
    ip_address = request.META.get('REMOTE_ADDR')
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        description=description,
        ip_address=ip_address
    )


@login_required
@user_passes_test(is_superuser)
def super_admin_dashboard(request):
    """Main dashboard for top-level system administrators"""
    
    # Get key statistics
    total_vikoba = Kikoba.objects.filter(is_active=True).count()
    total_members = User.objects.filter(is_active=True).count()
    total_investments = Investment.objects.count()
    active_investments = Investment.objects.filter(status='active').count()
    
    # Financial statistics
    total_loans = Loan.objects.aggregate(total=Sum('disbursed_amount'))['total'] or 0
    total_investment_value = Investment.objects.aggregate(total=Sum('current_amount'))['total'] or 0
    
    # Recent activities
    recent_vikoba = Kikoba.objects.order_by('-created_at')[:5]
    recent_investments = Investment.objects.order_by('-created_at')[:5]
    recent_logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:10]
    
    # Growth statistics (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_vikoba_count = Kikoba.objects.filter(created_at__gte=thirty_days_ago).count()
    new_members_count = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    
    # Investment performance
    investment_stats = Investment.objects.values('investment_type').annotate(
        count=Count('id'),
        total_amount=Sum('current_amount')
    )
    
    context = {
        'page_title': 'Super Admin Dashboard',
        'total_vikoba': total_vikoba,
        'total_members': total_members,
        'total_investments': total_investments,
        'active_investments': active_investments,
        'total_loans': total_loans,
        'total_investment_value': total_investment_value,
        'recent_vikoba': recent_vikoba,
        'recent_investments': recent_investments,
        'recent_logs': recent_logs,
        'new_vikoba_count': new_vikoba_count,
        'new_members_count': new_members_count,
        'investment_stats': investment_stats,
    }
    
    return render(request, 'dashboard/super_admin/dashboard.html', context)


@login_required
@user_passes_test(is_superuser)
def investment_list(request):
    """List all investments"""
    status_filter = request.GET.get('status', '')
    investment_type = request.GET.get('type', '')
    
    investments = Investment.objects.all()
    
    if status_filter:
        investments = investments.filter(status=status_filter)
    if investment_type:
        investments = investments.filter(investment_type=investment_type)
    
    paginator = Paginator(investments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Investment Management',
        'page_obj': page_obj,
        'status_filter': status_filter,
        'investment_type': investment_type,
        'investment_types': Investment.INVESTMENT_TYPE_CHOICES,
        'statuses': Investment.STATUS_CHOICES,
    }
    
    return render(request, 'dashboard/super_admin/investment_list.html', context)


@login_required
@user_passes_test(is_superuser)
def investment_create(request):
    """Create a new investment opportunity"""
    if request.method == 'POST':
        try:
            # Get form data
            post_data = request.POST
            
            # Parse key metrics, strengths, and risks from JSON strings
            import json
            key_metrics = json.loads(post_data.get('key_metrics', '[]'))
            strengths = json.loads(post_data.get('strengths', '[]'))
            risks = json.loads(post_data.get('risks', '[]'))
            
            # Get and validate required fields
            target_amount = post_data.get('target_amount')
            if not target_amount:
                messages.error(request, 'Target amount is required')
                raise ValueError('Target amount is required')
                
            # Create the investment with all required fields
            investment = Investment.objects.create(
                title=post_data.get('title'),
                description=post_data.get('description', ''),
                investment_type=post_data.get('investment_type', 'other'),
                status=post_data.get('status', 'draft'),
                risk_level=post_data.get('risk_level', 'medium'),
                minimum_amount=float(post_data.get('minimum_amount', 0) or 0),
                target_amount=float(target_amount),
                current_price=float(post_data.get('current_price', 0) or 0),
                expected_return_rate=float(post_data.get('expected_return_rate', 0) or 0),
                start_date=timezone.now().date(),  # Default to today
                end_date=timezone.now().date() + timezone.timedelta(days=365),  # Default 1 year
                duration_months=int(post_data.get('duration_months', 12) or 12),
                location=post_data.get('location', ''),
                available_to_all_vikoba=post_data.get('available_to_all_vikoba') == 'on',
                created_by=request.user,
                
                # Additional fields for the detailed description
                investment_thesis=post_data.get('investment_thesis', ''),
                key_metrics='\n'.join(key_metrics) if key_metrics else '',
                strengths='\n'.join(strengths) if strengths else '',
                risks='\n'.join(risks) if risks else '',
                source_url=post_data.get('source_url', ''),
                internal_notes=post_data.get('internal_notes', '')
            )
            
            # Handle file uploads
            if 'image' in request.FILES:
                investment.image = request.FILES['image']
                
            # Handle multiple document uploads
            if 'documents' in request.FILES:
                # For multiple file uploads, we'll handle them in a separate model
                for doc in request.FILES.getlist('documents'):
                    InvestmentDocument.objects.create(
                        investment=investment,
                        document=doc,
                        uploaded_by=request.user
                    )
            
            # Handle expiry date if provided
            if post_data.get('expiry_date'):
                from datetime import datetime
                try:
                    investment.end_date = datetime.strptime(post_data.get('expiry_date'), '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    pass
            
            investment.save()
            
            # Log the action
            log_admin_action(
                request.user, 'create', 'Investment', investment.id,
                f"Created investment: {investment.title}", request
            )
            
            messages.success(request, 'Investment opportunity created successfully!')
            return redirect('dashboard:super_admin:investment_detail', investment_id=investment.id)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error creating investment: {str(e)}')
    
    # For GET request or if there's an error in POST
    context = {
        'page_title': 'Create New Investment',
        'investment_types': Investment.INVESTMENT_TYPE_CHOICES,
        'statuses': Investment.STATUS_CHOICES,
        'risk_levels': [
            ('low', 'Low Risk'),
            ('medium', 'Medium Risk'),
            ('high', 'High Risk')
        ],
        'time_horizons': [
            ('short', 'Short-Term (< 3 years)'),
            ('medium', 'Medium-Term (3-10 years)'),
            ('long', 'Long-Term (10+ years)')
        ]
    }
    
    return render(request, 'dashboard/super_admin/investment_form.html', context)


@login_required
@user_passes_test(is_superuser)
def investment_edit(request, investment_id):
    """Edit an existing investment"""
    investment = get_object_or_404(Investment, id=investment_id)
    
    if request.method == 'POST':
        try:
            investment.title = request.POST.get('title')
            investment.description = request.POST.get('description')
            investment.investment_type = request.POST.get('investment_type')
            investment.status = request.POST.get('status')
            investment.risk_level = request.POST.get('risk_level')
            investment.minimum_amount = request.POST.get('minimum_amount')
            investment.maximum_amount = request.POST.get('maximum_amount') or None
            investment.target_amount = request.POST.get('target_amount')
            investment.expected_return_rate = request.POST.get('expected_return_rate')
            investment.start_date = request.POST.get('start_date')
            investment.end_date = request.POST.get('end_date')
            investment.duration_months = request.POST.get('duration_months')
            investment.location = request.POST.get('location', '')
            investment.available_to_all_vikoba = request.POST.get('available_to_all_vikoba') == 'on'
            
            # Handle image upload
            if 'image' in request.FILES:
                investment.image = request.FILES['image']
            
            # Handle documents upload
            if 'documents' in request.FILES:
                investment.documents = request.FILES['documents']
            
            investment.save()
            
            # Handle specific vikoba selection
            if not investment.available_to_all_vikoba:
                vikoba_ids = request.POST.getlist('specific_vikoba')
                investment.specific_vikoba.set(vikoba_ids)
            else:
                investment.specific_vikoba.clear()
            
            log_admin_action(
                request.user, 'update', 'Investment', investment.id,
                f"Updated investment: {investment.title}", request
            )
            
            messages.success(request, 'Investment updated successfully!')
            return redirect('dashboard:super_admin_investment_list')
        except Exception as e:
            messages.error(request, f'Error updating investment: {str(e)}')
    
    all_vikoba = Kikoba.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Edit Investment',
        'investment': investment,
        'investment_types': Investment.INVESTMENT_TYPE_CHOICES,
        'risk_levels': Investment.RISK_LEVEL_CHOICES,
        'statuses': Investment.STATUS_CHOICES,
        'all_vikoba': all_vikoba,
    }
    
    return render(request, 'dashboard/super_admin/investment_form.html', context)


@login_required
@user_passes_test(is_superuser)
def investment_detail(request, investment_id):
    """View investment details and participations"""
    investment = get_object_or_404(Investment, id=investment_id)
    participations = InvestmentParticipation.objects.filter(
        investment=investment
    ).select_related('kikoba')
    
    # Calculate statistics
    total_participations = participations.count()
    total_invested = participations.aggregate(total=Sum('amount_invested'))['total'] or 0
    total_returns = participations.aggregate(total=Sum('returns_received'))['total'] or 0
    
    context = {
        'page_title': f'Investment: {investment.title}',
        'investment': investment,
        'participations': participations,
        'total_participations': total_participations,
        'total_invested': total_invested,
        'total_returns': total_returns,
    }
    
    return render(request, 'dashboard/super_admin/investment_detail.html', context)


@login_required
@user_passes_test(is_superuser)
def vikoba_management(request):
    """Manage all vikoba in the system"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    vikoba = Kikoba.objects.all()
    
    if search_query:
        vikoba = vikoba.filter(
            Q(name__icontains=search_query) |
            Q(kikoba_number__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    if status_filter == 'active':
        vikoba = vikoba.filter(is_active=True)
    elif status_filter == 'inactive':
        vikoba = vikoba.filter(is_active=False)
    
    # Annotate with member counts
    vikoba = vikoba.annotate(
        member_count=Count('kikoba_memberships', filter=Q(kikoba_memberships__is_active=True))
    )
    
    paginator = Paginator(vikoba, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Vikoba Management',
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'dashboard/super_admin/vikoba_management.html', context)


@login_required
@user_passes_test(is_superuser)
def vikoba_detail(request, kikoba_id):
    """View detailed information about a specific kikoba"""
    kikoba = get_object_or_404(Kikoba, id=kikoba_id)
    members = KikobaMembership.objects.filter(kikoba=kikoba).select_related('user')
    
    # Statistics
    total_members = members.filter(is_active=True).count()
    admin_members = members.filter(role__in=['chairperson', 'treasurer', 'secretary'], is_active=True)
    
    context = {
        'page_title': f'Kikoba: {kikoba.name}',
        'kikoba': kikoba,
        'members': members,
        'total_members': total_members,
        'admin_members': admin_members,
    }
    
    return render(request, 'dashboard/super_admin/vikoba_detail.html', context)


@login_required
@user_passes_test(is_superuser)
def user_management(request):
    """Manage all users in the system"""
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    users = User.objects.all()
    
    if search_query:
        users = users.filter(
            Q(name__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'User Management',
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'role_choices': User.ROLE_CHOICES,
    }
    
    return render(request, 'dashboard/super_admin/user_management.html', context)


@login_required
@user_passes_test(is_superuser)
def system_notifications(request):
    """Create and manage system-wide notifications"""
    if request.method == 'POST':
        try:
            notification = SystemNotification.objects.create(
                title=request.POST.get('title'),
                message=request.POST.get('message'),
                priority=request.POST.get('priority'),
                send_to_all=request.POST.get('send_to_all') == 'on',
                created_by=request.user,
            )
            
            if not notification.send_to_all:
                vikoba_ids = request.POST.getlist('specific_vikoba')
                notification.specific_vikoba.set(vikoba_ids)
            
            log_admin_action(
                request.user, 'create', 'SystemNotification', notification.id,
                f"Created notification: {notification.title}", request
            )
            
            messages.success(request, 'Notification created successfully!')
            return redirect('dashboard:super_admin_notifications')
        except Exception as e:
            messages.error(request, f'Error creating notification: {str(e)}')
    
    notifications = SystemNotification.objects.order_by('-created_at')[:20]
    all_vikoba = Kikoba.objects.filter(is_active=True)
    
    context = {
        'page_title': 'System Notifications',
        'notifications': notifications,
        'all_vikoba': all_vikoba,
        'priorities': SystemNotification.PRIORITY_CHOICES,
    }
    
    return render(request, 'dashboard/super_admin/notifications.html', context)


@login_required
@user_passes_test(is_superuser)
def system_configuration(request):
    """Manage system-wide configuration settings"""
    if request.method == 'POST':
        key = request.POST.get('key')
        value = request.POST.get('value')
        description = request.POST.get('description', '')
        
        config, created = SystemConfiguration.objects.update_or_create(
            key=key,
            defaults={
                'value': value,
                'description': description,
                'updated_by': request.user,
            }
        )
        
        action = 'create' if created else 'update'
        log_admin_action(
            request.user, action, 'SystemConfiguration', config.id,
            f"{'Created' if created else 'Updated'} configuration: {key}", request
        )
        
        messages.success(request, f'Configuration {key} {"created" if created else "updated"} successfully!')
        return redirect('dashboard:super_admin_configuration')
    
    configurations = SystemConfiguration.objects.all()
    
    context = {
        'page_title': 'System Configuration',
        'configurations': configurations,
    }
    
    return render(request, 'dashboard/super_admin/configuration.html', context)


@login_required
@user_passes_test(is_superuser)
def audit_logs(request):
    """View system audit logs"""
    action_filter = request.GET.get('action', '')
    model_filter = request.GET.get('model', '')
    user_filter = request.GET.get('user', '')
    
    logs = AuditLog.objects.select_related('user').all()
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    if model_filter:
        logs = logs.filter(model_name=model_filter)
    if user_filter:
        logs = logs.filter(user_id=user_filter)
    
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique model names and users for filters
    model_names = AuditLog.objects.values_list('model_name', flat=True).distinct()
    users_with_logs = User.objects.filter(auditlog__isnull=False).distinct()
    
    context = {
        'page_title': 'Audit Logs',
        'page_obj': page_obj,
        'action_filter': action_filter,
        'model_filter': model_filter,
        'user_filter': user_filter,
        'action_choices': AuditLog.ACTION_CHOICES,
        'model_names': model_names,
        'users_with_logs': users_with_logs,
    }
    
    return render(request, 'dashboard/super_admin/audit_logs.html', context)


@login_required
@user_passes_test(is_superuser)
def reports_analytics(request):
    """Generate reports and analytics"""
    # Date range filters
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Default to last 30 days if no dates provided
    if not start_date or not end_date:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
    
    # Vikoba growth
    vikoba_growth = Kikoba.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).count()
    
    # User growth
    user_growth = User.objects.filter(
        date_joined__date__range=[start_date, end_date]
    ).count()
    
    # Investment statistics
    investment_data = Investment.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).aggregate(
        total_count=Count('id'),
        total_target=Sum('target_amount'),
        total_raised=Sum('current_amount')
    )
    
    context = {
        'page_title': 'Reports & Analytics',
        'start_date': start_date,
        'end_date': end_date,
        'vikoba_growth': vikoba_growth,
        'user_growth': user_growth,
        'investment_data': investment_data,
    }
    
    return render(request, 'dashboard/super_admin/reports.html', context)
