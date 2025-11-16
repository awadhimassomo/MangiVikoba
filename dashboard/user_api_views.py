from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import Coalesce

from loans.models import Loan, Repayment
from savings.models import Saving, Contribution
from groups.models import KikobaMembership

from .api_serializers import (
    LoanSerializer, RepaymentSerializer,
    SavingSerializer, ContributionSerializer,
    EmergencyFundSerializer, ShareContributionSerializer,
    KikobaSerializer
)

class UserLoansView(APIView):
    """
    Get all loans for the authenticated user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        loans = Loan.objects.filter(borrower=request.user).select_related('kikoba')
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            loans = loans.filter(status=status_filter.lower())
            
        serializer = LoanSerializer(loans, many=True)
        return Response({
            'status': 'success',
            'count': len(serializer.data),
            'data': serializer.data
        })

class UserLoanDetailView(APIView):
    """
    Get details of a specific loan for the authenticated user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, loan_id):
        try:
            loan = Loan.objects.get(id=loan_id, borrower=request.user)
            serializer = LoanSerializer(loan)
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        except Loan.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Loan not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )

class UserRepaymentsView(APIView):
    """
    Get all repayments for a specific loan (user must be the borrower)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, loan_id):
        repayments = Repayment.objects.filter(
            loan_id=loan_id,
            loan__borrower=request.user
        ).select_related('loan')
        
        serializer = RepaymentSerializer(repayments, many=True)
        return Response({
            'status': 'success',
            'count': len(serializer.data),
            'data': serializer.data
        })

class UserSavingsView(APIView):
    """
    Get all savings accounts for the authenticated user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        savings = Savings.objects.filter(member=request.user).select_related('kikoba')
        
        # Get total savings across all groups
        total_savings = savings.aggregate(
            total_balance=Coalesce(Sum('savings_balance'), 0),
            total_emergency_fund=Coalesce(Sum('emergency_fund_balance'), 0),
            total_shares=Coalesce(Sum('shares_purchased'), 0),
            total_shares_value=Coalesce(Sum('total_shares_value'), 0)
        )
        
        return Response({
            'status': 'success',
            'data': {
                'total_savings': total_savings['total_balance'],
                'total_emergency_fund': total_savings['total_emergency_fund'],
                'total_shares': total_savings['total_shares'],
                'total_shares_value': total_savings['total_shares_value'],
                'savings_accounts': [
                    {
                        'kikoba': KikobaSerializer(s.kikoba).data,
                        'savings_balance': s.savings_balance,
                        'emergency_fund_balance': s.emergency_fund_balance,
                        'shares_purchased': s.shares_purchased,
                        'share_price': s.share_price,
                        'total_shares_value': s.total_shares_value
                    } for s in savings
                ]
            }
        })

class UserSavingsTransactionsView(APIView):
    """
    Get all savings transactions (deposits and withdrawals) for the authenticated user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get deposits
        deposits = SavingsDeposit.objects.filter(
            member=request.user
        ).select_related('kikoba')
        
        # Get withdrawals
        withdrawals = SavingsWithdrawal.objects.filter(
            member=request.user
        ).select_related('kikoba')
        
        # Apply date filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            deposits = deposits.filter(deposit_date__gte=start_date)
            withdrawals = withdrawals.filter(withdrawal_date__gte=start_date)
            
        if end_date:
            deposits = deposits.filter(deposit_date__lte=end_date)
            withdrawals = withdrawals.filter(withdrawal_date__lte=end_date)
        
        # Serialize data
        deposit_serializer = SavingsDepositSerializer(deposits, many=True)
        withdrawal_serializer = SavingsWithdrawalSerializer(withdrawals, many=True)
        
        # Combine and sort transactions by date
        transactions = []
        
        for deposit in deposit_serializer.data:
            transactions.append({
                **deposit,
                'type': 'deposit',
                'date': deposit['deposit_date']
            })
            
        for withdrawal in withdrawal_serializer.data:
            transactions.append({
                **withdrawal,
                'type': 'withdrawal',
                'date': withdrawal['withdrawal_date']
            })
        
        # Sort by date (newest first)
        transactions.sort(key=lambda x: x['date'], reverse=True)
        
        return Response({
            'status': 'success',
            'count': len(transactions),
            'data': transactions
        })

class UserDashboardSummaryView(APIView):
    """
    Get a summary of the user's financial status across all Kikoba groups
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get all Kikoba groups the user is a member of
        kikoba_memberships = KikobaMember.objects.filter(member=user).select_related('kikoba')
        
        # Get total loans
        loans = Loan.objects.filter(borrower=user)
        total_loans = loans.aggregate(
            total_borrowed=Coalesce(Sum('amount'), 0),
            total_repaid=Coalesce(Sum('amount_paid'), 0),
            total_remaining=Coalesce(Sum('remaining_balance'), 0),
            active_loans=Count('id', filter=Q(status='active')),
            overdue_loans=Count('id', filter=Q(due_date__lt=timezone.now().date(), status='active'))
        )
        
        # Get total savings
        savings = Savings.objects.filter(member=user).aggregate(
            total_savings=Coalesce(Sum('savings_balance'), 0),
            total_emergency_fund=Coalesce(Sum('emergency_fund_balance'), 0),
            total_shares=Coalesce(Sum('shares_purchased'), 0),
            total_shares_value=Coalesce(Sum('total_shares_value'), 0)
        )
        
        # Get recent transactions (last 5)
        recent_deposits = SavingsDeposit.objects.filter(
            member=user
        ).order_by('-deposit_date')[:5]
        
        recent_withdrawals = SavingsWithdrawal.objects.filter(
            member=user
        ).order_by('-withdrawal_date')[:5]
        
        # Get upcoming loan payments (next 30 days)
        upcoming_payments = Repayment.objects.filter(
            loan__borrower=user,
            payment_date__gte=timezone.now().date(),
            payment_date__lte=timezone.now().date() + timedelta(days=30)
        ).select_related('loan').order_by('payment_date')
        
        return Response({
            'status': 'success',
            'data': {
                'user': {
                    'id': user.id,
                    'name': user.get_full_name(),
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'member_id': user.member_id
                },
                'kikoba_groups': [
                    {
                        'id': km.kikoba.id,
                        'name': km.kikoba.name,
                        'role': km.role,
                        'join_date': km.join_date
                    } for km in kikoba_memberships
                ],
                'loans': {
                    'total_borrowed': total_loans['total_borrowed'],
                    'total_repaid': total_loans['total_repaid'],
                    'total_remaining': total_loans['total_remaining'],
                    'active_loans': total_loans['active_loans'],
                    'overdue_loans': total_loans['overdue_loans']
                },
                'savings': {
                    'total_savings': savings['total_savings'],
                    'total_emergency_fund': savings['total_emergency_fund'],
                    'total_shares': savings['total_shares'],
                    'total_shares_value': savings['total_shares_value']
                },
                'recent_transactions': [
                    {
                        'type': 'deposit',
                        'amount': d.amount,
                        'date': d.deposit_date,
                        'kikoba': KikobaSerializer(d.kikoba).data
                    } for d in recent_deposits
                ] + [
                    {
                        'type': 'withdrawal',
                        'amount': w.amount,
                        'date': w.withdrawal_date,
                        'kikoba': KikobaSerializer(w.kikoba).data,
                        'status': w.status
                    } for w in recent_withdrawals
                ],
                'upcoming_payments': [
                    {
                        'id': p.id,
                        'amount': p.amount,
                        'due_date': p.payment_date,
                        'loan_id': p.loan.id,
                        'loan_purpose': p.loan.purpose,
                        'kikoba': KikobaSerializer(p.loan.kikoba).data
                    } for p in upcoming_payments
                ]
            }
        })
