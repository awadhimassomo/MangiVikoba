import csv
import io
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import View
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction
from django.template.loader import render_to_string
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from registration.models import User
from loans.models import Loan
from .forms import LoanImportForm

class LoanImportView(View):
    template_name = 'dashboard/loans/import_loans.html'
    form_class = LoanImportForm
    
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            kikoba = form.cleaned_data['kikoba']
            
            try:
                # Read the CSV file
                data = csv.DictReader(io.TextIOWrapper(csv_file, encoding='utf-8'))
                required_columns = ['member_id', 'amount', 'interest_rate', 'term_months', 'purpose', 'issue_date', 'due_date']
                
                # Check if all required columns are present
                if not all(column in data.fieldnames for column in required_columns):
                    messages.error(request, 'Invalid CSV format. Please download the template and try again.')
                    return render(request, self.template_name, {'form': form})
                
                success_count = 0
                error_messages = []
                
                with transaction.atomic():
                    for row_num, row in enumerate(data, 2):  # Start from row 2 (1-based index for error messages)
                        try:
                            member_id = row.get('member_id', '').strip()
                            if not member_id:
                                error_messages.append(f'Row {row_num}: Member ID is required')
                                continue
                                
                            # Get or create member
                            try:
                                member = User.objects.get(member_id=member_id, kikoba=kikoba)
                            except User.DoesNotExist:
                                error_messages.append(f'Row {row_num}: Member with ID {member_id} not found')
                                continue
                                
                            # Create loan
                            loan = Loan(
                                borrower=member,
                                kikoba=kikoba,
                                amount=float(row['amount']),
                                interest_rate=float(row['interest_rate']),
                                term_months=int(row['term_months']),
                                purpose=row['purpose'][:255],
                                issue_date=row['issue_date'],
                                due_date=row['due_date'],
                                status=row.get('status', 'active').lower(),
                                notes=row.get('notes', ''),
                                created_by=request.user,
                                is_legacy_import=True  # Mark as imported from legacy system
                            )
                            loan.save()
                            success_count += 1
                            
                        except Exception as e:
                            error_messages.append(f'Row {row_num}: {str(e)}')
                            continue
                
                if success_count > 0:
                    messages.success(request, f'Successfully imported {success_count} loans.')
                
                if error_messages:
                    messages.warning(request, f'Completed with {len(error_messages)} errors.')
                    request.session['import_errors'] = error_messages
                
                return redirect('dashboard:loan_list')
                
            except Exception as e:
                messages.error(request, f'Error processing CSV file: {str(e)}')
        
        return render(request, self.template_name, {'form': form})

def download_import_template(request):
    """View to download the CSV template"""
    template_path = 'dashboard/loans/loan_import_template.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="loan_import_template.csv"'
    
    # Generate the template content
    template_content = render_to_string(template_path)
    response.write(template_content)
    
    return response
