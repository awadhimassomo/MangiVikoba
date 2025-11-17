from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from django.utils import timezone
from datetime import datetime
import csv
import io

from groups.models import KikobaMembership, ShareContribution
from savings.models import Contribution


@login_required
def download_contributions_template(request):
    """Download a CSV template for bulk contribution upload"""
    admin_membership = KikobaMembership.objects.filter(
        user=request.user,
        role__in=['kikoba_admin', 'chairperson', 'treasurer'],
        is_active=True
    ).select_related('kikoba').first()
    
    if not admin_membership:
        messages.error(request, "You do not have administrative access.")
        return redirect('dashboard:home')
    
    current_kikoba = admin_membership.kikoba
    
    # Get parameters from request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    frequency = request.GET.get('frequency', 'monthly')
    
    # Generate periods if dates provided
    periods = []
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            current = start_date
            while current <= end_date:
                periods.append(current.strftime('%Y-%m-%d'))
                
                if frequency == 'monthly':
                    # Move to next month
                    if current.month == 12:
                        current = current.replace(year=current.year + 1, month=1)
                    else:
                        current = current.replace(month=current.month + 1)
                elif frequency == 'weekly':
                    from datetime import timedelta
                    current = current + timedelta(days=7)
                elif frequency == 'biweekly':
                    from datetime import timedelta
                    current = current + timedelta(days=14)
        except:
            # If date parsing fails, provide default template
            pass
    
    # If no periods, provide sample columns
    if not periods:
        periods = ['2024-01', '2024-02', '2024-03']  # Sample months
    
    # Get active members
    members = KikobaMembership.objects.filter(
        kikoba=current_kikoba,
        is_active=True
    ).select_related('user').order_by('user__name')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="contributions_template_{current_kikoba.name}_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Header row
    header = ['Member ID', 'Member Name', 'Phone Number'] + periods
    writer.writerow(header)
    
    # Member rows with empty contribution columns
    for member_item in members:
        row = [
            member_item.user.id,
            member_item.user.name,
            member_item.user.phone_number
        ] + [''] * len(periods)
        writer.writerow(row)
    
    # Instructions row (commented)
    writer.writerow([])
    writer.writerow(['# INSTRUCTIONS:'])
    writer.writerow(['# 1. Fill in contribution amounts in the date columns'])
    writer.writerow(['# 2. Leave blank if no contribution for that period'])
    writer.writerow(['# 3. Do NOT modify Member ID, Name, or Phone columns'])
    writer.writerow(['# 4. Save and upload this file'])
    
    return response


@login_required
def upload_contributions_csv(request):
    """Upload and process bulk contributions from CSV"""
    admin_membership = KikobaMembership.objects.filter(
        user=request.user,
        role__in=['kikoba_admin', 'chairperson', 'treasurer'],
        is_active=True
    ).select_related('kikoba').first()
    
    if not admin_membership:
        messages.error(request, "You do not have administrative access.")
        return redirect('dashboard:home')
    
    current_kikoba = admin_membership.kikoba
    
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        contribution_type = request.POST.get('contribution_type')
        
        if not csv_file:
            messages.error(request, "Please upload a CSV file.")
            return redirect('dashboard:csv_contributions_import')
        
        if not contribution_type:
            messages.error(request, "Please select a contribution type.")
            return redirect('dashboard:csv_contributions_import')
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Please upload a valid CSV file.")
            return redirect('dashboard:csv_contributions_import')
        
        try:
            # Read CSV file
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string)
            
            # Get header row
            header = next(reader)
            print(f"DEBUG: CSV Header: {header}")  # Debug log
            
            # Extract period dates (columns after the first 3)
            period_dates = header[3:]  # Skip Member ID, Name, Phone
            
            # Filter out instruction rows
            period_dates = [d for d in period_dates if d and not d.startswith('#')]
            print(f"DEBUG: Period dates found: {period_dates}")  # Debug log
            
            if not period_dates:
                messages.error(request, "No date columns found in CSV file. Please make sure your CSV has date columns after Member ID, Name, and Phone.")
                return redirect('dashboard:csv_contributions_import')
            
            # Process rows
            contributions_to_create = []
            share_contributions_to_create = []  # For ShareContribution records
            member_count = 0
            error_rows = []
            
            for row_num, row in enumerate(reader, start=2):
                # Skip empty rows or instruction rows
                if not row or (row[0] and row[0].startswith('#')):
                    continue
                
                try:
                    member_id = int(row[0])
                    member_name = row[1]
                    
                    # Get member from database
                    member_membership = KikobaMembership.objects.filter(
                        kikoba=current_kikoba,
                        user__id=member_id,
                        is_active=True
                    ).select_related('user').first()
                    
                    if not member_membership:
                        error_rows.append(f"Row {row_num}: Member ID {member_id} not found")
                        continue
                    
                    member = member_membership.user
                    member_count += 1
                    
                    # Process contribution amounts for each period
                    for i, period_date_str in enumerate(period_dates):
                        # Column index is 3 + i (after Member ID, Name, Phone)
                        col_index = 3 + i
                        
                        if col_index < len(row):
                            amount_str = row[col_index].strip()
                            
                            # Remove commas from amount (e.g., "50,000" -> "50000")
                            amount_str = amount_str.replace(',', '')
                            
                            if amount_str and amount_str.replace('.', '', 1).replace('-', '', 1).isdigit():
                                try:
                                    amount = float(amount_str)
                                except ValueError:
                                    continue  # Skip invalid amounts
                                
                                if amount > 0:
                                    # Parse period date - try multiple formats
                                    period_date = None
                                    date_formats = [
                                        '%Y-%m-%d',      # 2024-01-23
                                        '%m/%d/%Y',      # 1/23/2024
                                        '%d/%m/%Y',      # 23/1/2024
                                        '%Y/%m/%d',      # 2024/1/23
                                        '%m-%d-%Y',      # 1-23-2024
                                        '%d-%m-%Y',      # 23-1-2024
                                    ]
                                    
                                    for date_format in date_formats:
                                        try:
                                            period_date = datetime.strptime(period_date_str, date_format).date()
                                            break  # Successfully parsed
                                        except ValueError:
                                            continue  # Try next format
                                    
                                    if not period_date:
                                        error_rows.append(f"Row {row_num}: Invalid date format '{period_date_str}'. Please use YYYY-MM-DD or M/D/YYYY format.")
                                        continue
                                    
                                    # Create the appropriate contribution type
                                    if contribution_type == 'shares':
                                        # Create ShareContribution for shares
                                        share_amount = current_kikoba.contribution_config.share_amount if hasattr(current_kikoba, 'contribution_config') else amount
                                        share_contributions_to_create.append(
                                            ShareContribution(
                                                kikoba_membership=member_membership,
                                                amount_due=share_amount,
                                                amount_paid=amount,
                                                is_fully_paid=(amount >= share_amount),
                                                period_start=period_date,
                                                period_end=period_date,  # Same as start for CSV imports
                                            )
                                        )
                                    else:
                                        # Create regular Contribution for other types
                                        contributions_to_create.append(
                                            Contribution(
                                                member=member,
                                                kikoba=current_kikoba,
                                                amount=amount,
                                                date_contributed=period_date,
                                                transaction_reference=f"CSV_IMPORT_{contribution_type.upper()}_{period_date}",
                                                is_verified=True,
                                                verified_by=request.user,
                                                verified_at=timezone.now()
                                            )
                                        )
                
                except (ValueError, IndexError) as e:
                    error_rows.append(f"Row {row_num}: Error processing row - {str(e)}")
                    continue
            
            if error_rows:
                for error in error_rows[:10]:  # Show first 10 errors
                    messages.warning(request, error)
                if len(error_rows) > 10:
                    messages.warning(request, f"...and {len(error_rows) - 10} more errors")
            
            total_to_create = len(contributions_to_create) + len(share_contributions_to_create)
            print(f"DEBUG: Total contributions to create: {total_to_create}")  # Debug log
            print(f"DEBUG: Regular contributions: {len(contributions_to_create)}")  # Debug log
            print(f"DEBUG: Share contributions: {len(share_contributions_to_create)}")  # Debug log
            print(f"DEBUG: Member count: {member_count}")  # Debug log
            print(f"DEBUG: Errors: {len(error_rows)}")  # Debug log
            
            if total_to_create == 0:
                messages.error(request, f"No valid contributions found in the CSV file. Processed {member_count} members with {len(error_rows)} errors.")
                return redirect('dashboard:csv_contributions_import')
            
            # Bulk create contributions
            try:
                with transaction.atomic():
                    if contributions_to_create:
                        Contribution.objects.bulk_create(contributions_to_create)
                    if share_contributions_to_create:
                        ShareContribution.objects.bulk_create(share_contributions_to_create)
                    
                    success_msg = f"Successfully imported {total_to_create} contribution(s) for {member_count} member(s)!"
                    if contribution_type == 'shares':
                        success_msg += " (Share Contributions)"
                    messages.success(request, success_msg)
                    return redirect('dashboard:csv_contributions_import')
            
            except Exception as e:
                messages.error(request, f"Error saving contributions: {str(e)}")
                return redirect('dashboard:csv_contributions_import')
        
        except Exception as e:
            messages.error(request, f"Error processing CSV file: {str(e)}")
            return redirect('dashboard:csv_contributions_import')
    
    return redirect('dashboard:csv_contributions_import')


@login_required
def csv_contributions_import_view(request):
    """Main view for CSV contributions import"""
    admin_membership = KikobaMembership.objects.filter(
        user=request.user,
        role__in=['kikoba_admin', 'chairperson', 'treasurer'],
        is_active=True
    ).select_related('kikoba').first()
    
    if not admin_membership:
        messages.error(request, "You do not have administrative access.")
        return redirect('dashboard:home')
    
    current_kikoba = admin_membership.kikoba
    members = KikobaMembership.objects.filter(
        kikoba=current_kikoba,
        is_active=True
    ).select_related('user').order_by('user__name')
    
    # Get recent imports
    recent_contributions = Contribution.objects.filter(
        kikoba=current_kikoba,
        transaction_reference__startswith='CSV_IMPORT'
    ).select_related('member').order_by('-verified_at')[:20]
    
    context = {
        'page_title': f'CSV Contributions Import - {current_kikoba.name}',
        'current_kikoba': current_kikoba,
        'members': members,
        'recent_contributions': recent_contributions,
    }
    
    return render(request, 'dashboard/csv_contributions_import.html', context)
