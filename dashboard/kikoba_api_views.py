from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.db.models import Q

from loans.models import Loan, Repayment
from savings.models import Saving, Contribution
from groups.models import Kikoba, KikobaMembership
from registration.models import User
from .api_serializers import LoanSerializer, RepaymentSerializer, UserSerializer

class KikobaMemberLoansView(APIView):
    """
    API endpoint to get all loans for a specific member in a specific Kikoba group.
    Requires kikoba_id and member_id as URL parameters.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, kikoba_id, member_id):
        # Get the Kikoba and member
        kikoba = get_object_or_404(Kikoba, id=kikoba_id)
        member = get_object_or_404(User, id=member_id)
        
        # Verify the member belongs to this Kikoba
        if not KikobaMember.objects.filter(kikoba=kikoba, member=member).exists():
            return Response(
                {'status': 'error', 'message': 'Member not found in this Kikoba group'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all loans for this member in this Kikoba
        loans = Loan.objects.filter(
            kikoba=kikoba,
            borrower=member
        ).select_related('kikoba')
        
        # Apply filters if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            loans = loans.filter(status=status_filter.lower())
            
        # Get loan statistics
        loan_stats = loans.aggregate(
            total_loans=Count('id'),
            total_borrowed=Sum('amount'),
            total_repaid=Sum('amount_paid'),
            total_remaining=Sum('remaining_balance'),
            active_loans=Count('id', filter=Q(status='active')),
            overdue_loans=Count('id', filter=Q(status='overdue'))
        )
        
        serializer = LoanSerializer(loans, many=True)
        
        response_data = {
            'status': 'success',
            'kikoba': {
                'id': kikoba.id,
                'name': kikoba.name,
                'registration_number': kikoba.registration_number
            },
            'member': {
                'id': member.id,
                'name': member.get_full_name(),
                'member_id': member.member_id,
                'phone': member.phone_number
            },
            'stats': {
                'total_loans': loan_stats['total_loans'] or 0,
                'total_borrowed': float(loan_stats['total_borrowed'] or 0),
                'total_repaid': float(loan_stats['total_repaid'] or 0),
                'total_remaining': float(loan_stats['total_remaining'] or 0),
                'active_loans': loan_stats['active_loans'] or 0,
                'overdue_loans': loan_stats['overdue_loans'] or 0
            },
            'loans': serializer.data
        }
        
        return Response(response_data)

class KikobaMemberLoanDetailView(APIView):
    """
    API endpoint to get details of a specific loan for a member in a Kikoba.
    Requires kikoba_id, member_id, and loan_id as URL parameters.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, kikoba_id, member_id, loan_id):
        # Get the Kikoba, member, and loan
        kikoba = get_object_or_404(Kikoba, id=kikoba_id)
        member = get_object_or_404(User, id=member_id)
        
        # Verify the member belongs to this Kikoba
        if not KikobaMember.objects.filter(kikoba=kikoba, member=member).exists():
            return Response(
                {'status': 'error', 'message': 'Member not found in this Kikoba group'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get the loan and verify it belongs to this member and Kikoba
        loan = get_object_or_404(
            Loan,
            id=loan_id,
            kikoba=kikoba,
            borrower=member
        )
        
        # Get all repayments for this loan
        repayments = Repayment.objects.filter(loan=loan).order_by('payment_date')
        
        loan_serializer = LoanSerializer(loan)
        repayment_serializer = RepaymentSerializer(repayments, many=True)
        
        response_data = {
            'status': 'success',
            'loan': loan_serializer.data,
            'repayments': {
                'count': repayments.count(),
                'total_paid': float(repayments.aggregate(total=Sum('amount'))['total'] or 0),
                'transactions': repayment_serializer.data
            }
        }
        
        return Response(response_data)
