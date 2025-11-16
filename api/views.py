from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.reverse import reverse
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum
from django_filters.rest_framework import DjangoFilterBackend
import logging

logger = logging.getLogger(__name__)

from groups.models import (
    Kikoba, KikobaMembership, KikobaInvitation,
    KikobaContributionConfig, EntryFeePayment,
    ShareContribution, EmergencyFundContribution
)
from savings.models import Saving, KikobaBalance, MemberBalance, SavingCycle, Contribution
from loans.models import LoanProduct, LoanApplication, Loan, Repayment
from notifications.models import Notification

from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    KikobaSerializer, KikobaMembershipSerializer, KikobaInvitationSerializer,
    KikobaContributionConfigSerializer, SavingSerializer, ContributionSerializer,
    KikobaBalanceSerializer, MemberBalanceSerializer, SavingCycleSerializer,
    LoanProductSerializer, LoanApplicationSerializer, LoanApplicationCreateSerializer, LoanSerializer,
    RepaymentSerializer, NotificationSerializer, EntryFeePaymentSerializer,
    ShareContributionSerializer, EmergencyFundContributionSerializer, LoanGuarantorSerializer
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that uses phone_number instead of username
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        print("\n" + "="*60)
        print("=== TOKEN REQUEST ===")
        print(f"Request method: {request.method}")
        print(f"Request content type: {request.content_type}")
        print(f"Request data: {request.data}")
        print(f"Serializer class: {self.serializer_class}")
        print(f"Expected username field: {self.serializer_class.username_field}")
        print("="*60)
        
        response = super().post(request, *args, **kwargs)
        
        print(f"\nResponse status: {response.status_code}")
        if response.status_code != 200:
            print(f"ERROR - Response data: {response.data}")
        print("="*60 + "\n")
        
        return response


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request, format=None):
    """
    MangiVikoba REST API Root
    
    Welcome to the MangiVikoba API. This API provides comprehensive access to:
    - User management
    - Vikoba (savings group) operations
    - Savings and contributions tracking
    - Loan management
    - Notifications
    
    Authentication required for all endpoints except registration and login.
    Use JWT tokens in the Authorization header: Bearer {token}
    """
    return Response({
        'message': 'Welcome to MangiVikoba REST API v1',
        'version': '1.0.0',
        'authentication': {
            'login': reverse('token_obtain_pair', request=request, format=format),
            'refresh': reverse('token_refresh', request=request, format=format),
            'verify': reverse('token_verify', request=request, format=format),
        },
        'endpoints': {
            'users': reverse('user-list', request=request, format=format),
            'vikoba': reverse('kikoba-list', request=request, format=format),
            'memberships': reverse('membership-list', request=request, format=format),
            'invitations': reverse('invitation-list', request=request, format=format),
            'savings': reverse('saving-list', request=request, format=format),
            'contributions': reverse('contribution-list', request=request, format=format),
            'member_balances': reverse('member-balance-list', request=request, format=format),
            'kikoba_balances': reverse('kikoba-balance-list', request=request, format=format),
            'saving_cycles': reverse('saving-cycle-list', request=request, format=format),
            'loan_products': reverse('loan-product-list', request=request, format=format),
            'loan_applications': reverse('loan-application-list', request=request, format=format),
            'loans': reverse('loan-list', request=request, format=format),
            'repayments': reverse('repayment-list', request=request, format=format),
            'notifications': reverse('notification-list', request=request, format=format),
            'entry_fee_payments': reverse('entry-fee-payment-list', request=request, format=format),
            'share_contributions': reverse('share-contribution-list', request=request, format=format),
            'emergency_fund_contributions': reverse('emergency-fund-contribution-list', request=request, format=format),
        },
        'documentation': 'See API_DOCUMENTATION.md for complete reference',
        'note': 'Most endpoints require authentication. Register at /users/ or login at /auth/token/'
    })


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'phone_number', 'email']
    ordering_fields = ['date_joined', 'name']
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_vikoba(self, request):
        """Get all vikoba where current user is a member"""
        memberships = KikobaMembership.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('kikoba')
        vikoba = [membership.kikoba for membership in memberships]
        serializer = KikobaSerializer(vikoba, many=True)
        return Response(serializer.data)


class KikobaViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Kikoba (Groups)
    """
    queryset = Kikoba.objects.all()
    serializer_class = KikobaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_center_kikoba', 'contribution_frequency']
    search_fields = ['name', 'kikoba_number', 'location']
    ordering_fields = ['created_at', 'name']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get all members of a kikoba"""
        kikoba = self.get_object()
        memberships = kikoba.kikoba_memberships.filter(is_active=True)
        serializer = KikobaMembershipSerializer(memberships, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Get kikoba balance"""
        kikoba = self.get_object()
        try:
            balance = kikoba.kikoba_balance_detail
            balance.update_balance()
            serializer = KikobaBalanceSerializer(balance)
            return Response(serializer.data)
        except KikobaBalance.DoesNotExist:
            return Response(
                {"detail": "Balance not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a kikoba"""
        kikoba = self.get_object()
        user = request.user
        
        # Check if already a member
        if KikobaMembership.objects.filter(kikoba=kikoba, user=user).exists():
            return Response(
                {"detail": "Already a member"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        membership = KikobaMembership.objects.create(
            kikoba=kikoba,
            user=user,
            role='member'
        )
        serializer = KikobaMembershipSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def member_totals(self, request, pk=None):
        """
        Calculate and return member totals/payouts based on kikoba type.
        This endpoint demonstrates how different kikoba types affect member payouts.
        """
        from decimal import Decimal
        from finance import (
            MemberContribution,
            StandardVikoba,
            FixedShareVikoba,
            InterestRefundVikoba,
            RoscaModel
        )
        
        kikoba = self.get_object()
        memberships = kikoba.kikoba_memberships.filter(is_active=True)
        
        if not memberships.exists():
            return Response(
                {"detail": "No active members in this kikoba"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get financial data from database
        # For now, we'll use aggregated data. In production, this should come from actual transactions
        total_interest_collected = Decimal('0')
        total_fines_collected = Decimal('0')
        
        # Aggregate interest from loan repayments
        from loans.models import Repayment
        interest_data = Repayment.objects.filter(
            loan__application__kikoba=kikoba,
            is_verified=True
        ).aggregate(total_interest=Sum('interest_amount'))
        if interest_data['total_interest']:
            total_interest_collected = Decimal(str(interest_data['total_interest']))
        
        # Aggregate fines (you can add fine model when implemented)
        # For now, we'll use a sample value
        total_fines_collected = Decimal('5000.00')  # Sample value
        
        # Build member contributions list
        members = []
        member_details = []
        
        for membership in memberships:
            # Get member's share contributions
            share_total = ShareContribution.objects.filter(
                kikoba_membership=membership
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
            
            # Get member's entry fee
            entry_fee = EntryFeePayment.objects.filter(
                kikoba_membership=membership
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
            
            # Get member's emergency fund contributions
            emergency_fund = EmergencyFundContribution.objects.filter(
                kikoba_membership=membership
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Calculate total fixed contribution
            fixed_contribution = share_total + entry_fee + emergency_fund
            
            # Get interest paid by this member on their loans
            interest_paid = Repayment.objects.filter(
                loan__application__member=membership.user,
                loan__application__kikoba=kikoba,
                is_verified=True
            ).aggregate(total=Sum('interest_amount'))['total'] or Decimal('0')
            interest_paid = Decimal(str(interest_paid))
            
            # For standard vikoba, calculate shares based on contribution
            # Assuming 1 share = 10,000 TZS (you can adjust this)
            share_value = Decimal('10000')
            shares = share_total / share_value if share_total > 0 else Decimal('0')
            
            member_contrib = MemberContribution(
                member_id=membership.user.id,
                shares=shares,
                fixed_contribution=fixed_contribution,
                interest_paid=interest_paid,
                fines_paid=Decimal('0')
            )
            members.append(member_contrib)
            
            member_details.append({
                'user_id': membership.user.id,
                'name': membership.user.name,
                'phone_number': membership.user.phone_number,
                'shares': float(shares),
                'fixed_contribution': float(fixed_contribution),
                'interest_paid': float(interest_paid)
            })
        
        # Calculate payouts based on kikoba type
        kikoba_type = kikoba.group_type or 'standard'
        
        if kikoba_type == 'standard':
            payouts = StandardVikoba.calculate_payouts(
                members, total_interest_collected, total_fines_collected
            )
            calculation_method = 'Proportional to shares (more shares = more profit)'
        elif kikoba_type == 'fixed_share':
            payouts = FixedShareVikoba.calculate_payouts(
                members, total_interest_collected, total_fines_collected
            )
            calculation_method = 'Equal distribution among all members'
        elif kikoba_type == 'interest_refund':
            payouts = InterestRefundVikoba.calculate_payouts(
                members, total_interest_collected, total_fines_collected
            )
            calculation_method = 'Interest refunded to borrowers + equal share of fines'
        elif kikoba_type == 'rosca':
            # ROSCA doesn't use the same payout calculation
            contribution_per_member = Decimal('50000')  # Sample value
            pot_size = RoscaModel.calculate_pot_size(
                float(contribution_per_member), len(members)
            )
            payouts = {}  # ROSCA payouts rotate
            calculation_method = f'Rotating pot of {pot_size:,.2f} TZS per meeting'
        else:
            payouts = {}
            calculation_method = 'Unknown kikoba type'
        
        # Format the response
        member_payouts = []
        for detail in member_details:
            user_id = detail['user_id']
            payout = float(payouts.get(user_id, Decimal('0')))
            profit = payout - detail['fixed_contribution']
            
            member_payouts.append({
                'user_id': user_id,
                'name': detail['name'],
                'phone_number': detail['phone_number'],
                'contribution': detail['fixed_contribution'],
                'shares': detail['shares'],
                'interest_paid': detail['interest_paid'],
                'total_payout': payout,
                'profit': profit
            })
        
        response_data = {
            'kikoba': {
                'id': kikoba.id,
                'name': kikoba.name,
                'kikoba_number': kikoba.kikoba_number,
                'group_type': kikoba_type,
                'group_type_display': kikoba.get_group_type_display() if kikoba.group_type else 'Standard VIKOBA'
            },
            'financial_summary': {
                'total_interest_collected': float(total_interest_collected),
                'total_fines_collected': float(total_fines_collected),
                'total_profit': float(total_interest_collected + total_fines_collected),
                'calculation_method': calculation_method
            },
            'members': member_payouts,
            'summary': {
                'total_members': len(member_payouts),
                'total_contributions': sum(m['contribution'] for m in member_payouts),
                'total_payouts': sum(m['total_payout'] for m in member_payouts),
                'total_profit_distributed': sum(m['profit'] for m in member_payouts)
            }
        }
        
        return Response(response_data)
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def debug_headers(self, request, pk=None):
        """Debug endpoint to see what headers are being received"""
        headers_dict = {}
        for header, value in request.META.items():
            if header.startswith('HTTP_') or header in ['CONTENT_TYPE', 'CONTENT_LENGTH']:
                headers_dict[header] = value
        
        return Response({
            'message': 'Headers received by backend',
            'all_headers': headers_dict,
            'has_authorization': 'HTTP_AUTHORIZATION' in request.META,
            'authorization_value': request.META.get('HTTP_AUTHORIZATION', 'NOT PROVIDED'),
            'user_is_authenticated': request.user.is_authenticated,
            'user': str(request.user),
            'kikoba_id': pk
        })
    
    @action(detail=True, methods=['get'])
    def test_auth(self, request, pk=None):
        """Simple test endpoint to verify authentication is working"""
        return Response({
            'message': 'Authentication works!',
            'user': request.user.phone_number if request.user.is_authenticated else 'Anonymous',
            'is_authenticated': request.user.is_authenticated,
            'kikoba_id': pk
        })
    
    @action(
        detail=True, 
        methods=['get'], 
        permission_classes=[IsAuthenticated],
        authentication_classes=[JWTAuthentication]
    )
    def my_total(self, request, pk=None):
        """
        Get the total/payout for the currently logged-in user in this specific kikoba.
        This endpoint is user-specific and only shows their own financial data.
        """
        # Debug logging
        logger.info(f"my_total endpoint called - User: {request.user}, Is authenticated: {request.user.is_authenticated}")
        logger.info(f"Authorization header: {request.headers.get('Authorization', 'Not provided')}")
        
        from decimal import Decimal
        from finance import (
            MemberContribution,
            StandardVikoba,
            FixedShareVikoba,
            InterestRefundVikoba,
            RoscaModel
        )
        
        kikoba = self.get_object()
        user = request.user
        
        # Check if user is a member of this kikoba
        try:
            membership = KikobaMembership.objects.get(
                kikoba=kikoba,
                user=user,
                is_active=True
            )
        except KikobaMembership.DoesNotExist:
            return Response(
                {"detail": "You are not a member of this kikoba"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all active members for calculation context
        all_memberships = kikoba.kikoba_memberships.filter(is_active=True)
        
        # Get financial data from database - NO PLACEHOLDERS!
        logger.info("="*80)
        logger.info(f"CALCULATING TOTALS FOR KIKOBA: {kikoba.name} (ID: {kikoba.id})")
        logger.info(f"User: {user.name} (ID: {user.id})")
        logger.info("="*80)
        
        total_interest_collected = Decimal('0')
        total_fines_collected = Decimal('0')
        
        # Aggregate interest from loan repayments
        from loans.models import Repayment, Loan
        total_repayments = Repayment.objects.filter(
            loan__application__kikoba=kikoba,
            is_verified=True
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
        
        logger.info(f"Total Verified Repayments: {total_repayments:,.2f} TZS")
        
        # Calculate actual interest from loans
        # Get all loans for this kikoba
        kikoba_loans = Loan.objects.filter(application__kikoba=kikoba, status='disbursed')
        total_principal = kikoba_loans.aggregate(total=Sum('disbursed_amount'))['total'] or Decimal('0')
        
        # Interest = Total Repayments - Total Principal
        total_interest_collected = max(total_repayments - total_principal, Decimal('0'))
        logger.info(f"Total Principal Loaned: {total_principal:,.2f} TZS")
        logger.info(f"Total Interest Collected: {total_interest_collected:,.2f} TZS")
        
        # TODO: Add Fines model to track actual fines
        # For now, fines are 0 until fines are tracked in database
        total_fines_collected = Decimal('0')  # Real value from database (currently no fines recorded)
        logger.info(f"Total Fines Collected: {total_fines_collected:,.2f} TZS")
        
        # Build member contributions list for all members (needed for calculation)
        members = []
        
        for mem in all_memberships:
            # Get member's share contributions
            share_total = ShareContribution.objects.filter(
                kikoba_membership=mem
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
            
            # Get member's entry fee
            entry_fee = EntryFeePayment.objects.filter(
                kikoba_membership=mem
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
            
            # Get member's emergency fund contributions (NOT reclaimable)
            emergency_fund = EmergencyFundContribution.objects.filter(
                kikoba_membership=mem
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Calculate total RECLAIMABLE contribution (excluding emergency fund)
            # Emergency fund stays with the kikoba and is not part of payouts
            fixed_contribution = share_total + entry_fee
            
            # Get interest paid by this member on their loans
            member_repayments = Repayment.objects.filter(
                loan__application__member=mem.user,
                loan__application__kikoba=kikoba,
                is_verified=True
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
            
            # Get principal borrowed by this member
            member_loans = Loan.objects.filter(
                application__member=mem.user,
                application__kikoba=kikoba,
                status='disbursed'
            ).aggregate(total=Sum('disbursed_amount'))['total'] or Decimal('0')
            
            # Actual interest = Repayments - Principal
            interest_paid = max(Decimal(str(member_repayments)) - Decimal(str(member_loans)), Decimal('0'))
            
            if mem.user.id == user.id:
                logger.info(f"\n--- {mem.user.name}'s Contributions ---")
                logger.info(f"  Share Contributions: {share_total:,.2f} TZS")
                logger.info(f"  Entry Fee: {entry_fee:,.2f} TZS")
                logger.info(f"  Emergency Fund: {emergency_fund:,.2f} TZS (NOT reclaimable)")
                logger.info(f"  RECLAIMABLE Contribution: {fixed_contribution:,.2f} TZS")
                logger.info(f"  Loans Taken: {member_loans:,.2f} TZS")
                logger.info(f"  Total Repayments: {member_repayments:,.2f} TZS")
                logger.info(f"  Interest Paid: {interest_paid:,.2f} TZS")
            
            # Calculate shares
            share_value = Decimal('10000')
            shares = share_total / share_value if share_total > 0 else Decimal('0')
            
            member_contrib = MemberContribution(
                member_id=mem.user.id,
                shares=shares,
                fixed_contribution=fixed_contribution,
                interest_paid=interest_paid,
                fines_paid=Decimal('0')
            )
            members.append(member_contrib)
        
        # Calculate payouts based on kikoba type
        kikoba_type = kikoba.group_type or 'standard'
        
        if kikoba_type == 'standard':
            payouts = StandardVikoba.calculate_payouts(
                members, total_interest_collected, total_fines_collected
            )
            calculation_method = 'Proportional to shares (more shares = more profit)'
        elif kikoba_type == 'fixed_share':
            payouts = FixedShareVikoba.calculate_payouts(
                members, total_interest_collected, total_fines_collected
            )
            calculation_method = 'Equal distribution among all members'
        elif kikoba_type == 'interest_refund':
            payouts = InterestRefundVikoba.calculate_payouts(
                members, total_interest_collected, total_fines_collected
            )
            calculation_method = 'Interest refunded to borrowers + equal share of fines'
        elif kikoba_type == 'rosca':
            contribution_per_member = Decimal('50000')
            pot_size = RoscaModel.calculate_pot_size(
                float(contribution_per_member), len(members)
            )
            payouts = {}
            calculation_method = f'Rotating pot of {pot_size:,.2f} TZS per meeting'
        else:
            payouts = {}
            calculation_method = 'Unknown kikoba type'
        
        # Get user's specific data
        user_contribution = next(
            (m for m in members if m.member_id == user.id), None
        )
        
        if not user_contribution:
            return Response(
                {"detail": "Could not find your contribution data"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        user_payout = float(payouts.get(user.id, Decimal('0')))
        user_profit = user_payout - float(user_contribution.fixed_contribution)
        
        logger.info(f"\n--- FINAL CALCULATION FOR {user.name} ---")
        logger.info(f"  Total Contribution: {user_contribution.fixed_contribution:,.2f} TZS")
        logger.info(f"  Interest Paid (Refunded): {user_contribution.interest_paid:,.2f} TZS")
        logger.info(f"  Fine Share: {total_fines_collected / Decimal(str(len(members))):,.2f} TZS")
        logger.info(f"  Total Payout: {user_payout:,.2f} TZS")
        logger.info(f"  Profit: {user_profit:,.2f} TZS")
        logger.info(f"  Calculation: {user_contribution.fixed_contribution} + {user_contribution.interest_paid} + {total_fines_collected / Decimal(str(len(members)))} = {user_payout}")
        logger.info("="*80)
        
        response_data = {
            'kikoba': {
                'id': kikoba.id,
                'name': kikoba.name,
                'kikoba_number': kikoba.kikoba_number,
                'group_type': kikoba_type,
                'group_type_display': kikoba.get_group_type_display() if kikoba.group_type else 'Standard VIKOBA'
            },
            'membership': {
                'membership_id': membership.id,
                'role': membership.role,
                'joined_at': membership.joined_at.isoformat()
            },
            'user': {
                'id': user.id,
                'name': user.name,
                'phone_number': user.phone_number
            },
            'financial_data': {
                'contribution': float(user_contribution.fixed_contribution),
                'shares': float(user_contribution.shares),
                'interest_paid_on_loans': float(user_contribution.interest_paid),
                'total_payout': user_payout,
                'profit': user_profit
            },
            'kikoba_summary': {
                'total_members': len(members),
                'total_interest_collected': float(total_interest_collected),
                'total_fines_collected': float(total_fines_collected),
                'calculation_method': calculation_method
            },
            'message': f'Your total payout in {kikoba.name} is {user_payout:,.2f} TZS (Profit: {user_profit:,.2f} TZS)'
        }
        
        return Response(response_data)
    
    @action(
        detail=True, 
        methods=['get'], 
        permission_classes=[IsAuthenticated],
        authentication_classes=[JWTAuthentication]
    )
    def my_loans(self, request, pk=None):
        """
        Get the currently logged-in user's loans in this specific kikoba.
        Returns loan details including
        principal, repayments, and interest.
        """
        from decimal import Decimal
        from loans.models import Loan, LoanApplication, Repayment
        
        kikoba = self.get_object()
        user = request.user
        
        # Check if user is a member of this kikoba
        try:
            membership = KikobaMembership.objects.get(
                kikoba=kikoba,
                user=user,
                is_active=True
            )
        except KikobaMembership.DoesNotExist:
            return Response(
                {"detail": "You are not a member of this kikoba"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get user's loans in this kikoba
        user_loans = Loan.objects.filter(
            application__member=user,
            application__kikoba=kikoba
        ).select_related('application')
        
        loans_data = []
        total_borrowed = Decimal('0')
        total_repaid = Decimal('0')
        total_interest_paid = Decimal('0')
        
        for loan in user_loans:
            # Get repayments for this loan
            repayments = Repayment.objects.filter(loan=loan, is_verified=True)
            loan_repaid = repayments.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
            
            principal = loan.disbursed_amount or Decimal('0')
            interest_paid = max(loan_repaid - principal, Decimal('0'))
            
            total_borrowed += principal
            total_repaid += loan_repaid
            total_interest_paid += interest_paid
            
            loans_data.append({
                'loan_id': loan.id,
                'disbursement_date': loan.disbursement_date.isoformat() if loan.disbursement_date else None,
                'principal': float(principal),
                'interest_rate': float(loan.interest_rate_at_disbursement or 0),
                'total_repayable': float(loan.total_repayable or 0),
                'amount_repaid': float(loan_repaid),
                'interest_paid': float(interest_paid),
                'status': loan.status,
                'due_date': loan.current_due_date.isoformat() if loan.current_due_date else None
            })
        
        return Response({
            'kikoba': {
                'id': kikoba.id,
                'name': kikoba.name,
                'kikoba_number': kikoba.kikoba_number
            },
            'user': {
                'id': user.id,
                'name': user.name,
                'phone_number': user.phone_number
            },
            'summary': {
                'total_loans': len(loans_data),
                'total_borrowed': float(total_borrowed),
                'total_repaid': float(total_repaid),
                'total_interest_paid': float(total_interest_paid),
                'outstanding_balance': float(total_borrowed - total_repaid)
            },
            'loans': loans_data
        })
    
    @action(
        detail=True, 
        methods=['get'], 
        permission_classes=[IsAuthenticated],
        authentication_classes=[JWTAuthentication]
    )
    def my_shares(self, request, pk=None):
        """
        Get the currently logged-in user's share contributions in this specific kikoba.
        """
        from decimal import Decimal
        
        kikoba = self.get_object()
        user = request.user
        
        # Check if user is a member of this kikoba
        try:
            membership = KikobaMembership.objects.get(
                kikoba=kikoba,
                user=user,
                is_active=True
            )
        except KikobaMembership.DoesNotExist:
            return Response(
                {"detail": "You are not a member of this kikoba"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get share contributions
        share_contributions = ShareContribution.objects.filter(
            kikoba_membership=membership
        ).order_by('-payment_date')
        
        contributions_data = []
        total_shares = Decimal('0')
        
        for contribution in share_contributions:
            contributions_data.append({
                'id': contribution.id,
                'amount': float(contribution.amount_paid),
                'payment_date': contribution.payment_date.isoformat(),
                'number_of_shares': float(contribution.number_of_shares or 0),
                'is_verified': contribution.is_verified
            })
            total_shares += contribution.amount_paid
        
        # Calculate number of shares (assuming share_value from kikoba settings)
        share_value = Decimal('10000')  # Default share value
        number_of_shares = total_shares / share_value if total_shares > 0 else Decimal('0')
        
        return Response({
            'kikoba': {
                'id': kikoba.id,
                'name': kikoba.name,
                'kikoba_number': kikoba.kikoba_number
            },
            'user': {
                'id': user.id,
                'name': user.name,
                'phone_number': user.phone_number
            },
            'summary': {
                'total_amount': float(total_shares),
                'number_of_shares': float(number_of_shares),
                'share_value': float(share_value),
                'total_contributions': len(contributions_data)
            },
            'contributions': contributions_data
        })
    
    @action(
        detail=True, 
        methods=['get'], 
        permission_classes=[IsAuthenticated],
        authentication_classes=[JWTAuthentication]
    )
    def my_emergency_fund(self, request, pk=None):
        """
        Get the currently logged-in user's emergency fund contributions in this specific kikoba.
        Note: Emergency fund is NOT reclaimable - it stays with the kikoba.
        """
        from decimal import Decimal
        
        kikoba = self.get_object()
        user = request.user
        
        # Check if user is a member of this kikoba
        try:
            membership = KikobaMembership.objects.get(
                kikoba=kikoba,
                user=user,
                is_active=True
            )
        except KikobaMembership.DoesNotExist:
            return Response(
                {"detail": "You are not a member of this kikoba"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get emergency fund contributions
        emergency_contributions = EmergencyFundContribution.objects.filter(
            kikoba_membership=membership
        ).order_by('-contribution_date')
        
        contributions_data = []
        total_emergency_fund = Decimal('0')
        
        for contribution in emergency_contributions:
            contributions_data.append({
                'id': contribution.id,
                'amount': float(contribution.amount),
                'contribution_date': contribution.contribution_date.isoformat(),
                'notes': contribution.notes or ''
            })
            total_emergency_fund += contribution.amount
        
        return Response({
            'kikoba': {
                'id': kikoba.id,
                'name': kikoba.name,
                'kikoba_number': kikoba.kikoba_number
            },
            'user': {
                'id': user.id,
                'name': user.name,
                'phone_number': user.phone_number
            },
            'summary': {
                'total_amount': float(total_emergency_fund),
                'total_contributions': len(contributions_data),
                'is_reclaimable': False,
                'note': 'Emergency fund stays with the kikoba and is not part of member payouts'
            },
            'contributions': contributions_data
        })


class KikobaMembershipViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Kikoba memberships
    """
    queryset = KikobaMembership.objects.all()
    serializer_class = KikobaMembershipSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['kikoba', 'user', 'role', 'is_active']
    ordering_fields = ['joined_at']
    
    def get_queryset(self):
        """Filter to show only memberships for current user or their kikoba"""
        user = self.request.user
        return KikobaMembership.objects.filter(
            Q(user=user) | Q(kikoba__created_by=user)
        )


class KikobaInvitationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Kikoba invitations
    """
    queryset = KikobaInvitation.objects.all()
    serializer_class = KikobaInvitationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['kikoba', 'status']
    ordering_fields = ['created_at']
    
    def perform_create(self, serializer):
        serializer.save(invited_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept an invitation"""
        invitation = self.get_object()
        
        if invitation.status != 'pending':
            return Response(
                {"detail": "Invitation already processed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invitation.status = 'accepted'
        invitation.save()
        
        # Create membership
        KikobaMembership.objects.create(
            kikoba=invitation.kikoba,
            user=request.user,
            role='member'
        )
        
        return Response({"detail": "Invitation accepted"})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject an invitation"""
        invitation = self.get_object()
        
        if invitation.status != 'pending':
            return Response(
                {"detail": "Invitation already processed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invitation.status = 'rejected'
        invitation.save()
        
        return Response({"detail": "Invitation rejected"})


class SavingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Savings
    """
    queryset = Saving.objects.all()
    serializer_class = SavingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['group', 'member', 'status']
    ordering_fields = ['transaction_date']
    
    def get_queryset(self):
        """Filter savings for user's vikoba"""
        user = self.request.user
        return Saving.objects.filter(
            Q(member=user) | Q(group__memberships__user=user)
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a saving transaction"""
        saving = self.get_object()
        saving.confirm(confirmed_by=request.user)
        serializer = self.get_serializer(saving)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a saving transaction"""
        saving = self.get_object()
        saving.reject(confirmed_by=request.user)
        serializer = self.get_serializer(saving)
        return Response(serializer.data)


class ContributionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Contributions
    """
    queryset = Contribution.objects.all()
    serializer_class = ContributionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['kikoba', 'member', 'saving_cycle', 'is_verified']
    ordering_fields = ['date_contributed']
    
    def get_queryset(self):
        """Filter contributions for user's vikoba"""
        user = self.request.user
        return Contribution.objects.filter(
            Q(member=user) | Q(kikoba__memberships__user=user)
        ).distinct()


class MemberBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Member Balances (read-only)
    """
    queryset = MemberBalance.objects.all()
    serializer_class = MemberBalanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['group', 'member']
    
    def get_queryset(self):
        """Filter balances for user's vikoba"""
        user = self.request.user
        return MemberBalance.objects.filter(
            Q(member=user) | Q(group__memberships__user=user)
        ).distinct()


class KikobaBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Kikoba Balances (read-only)
    """
    queryset = KikobaBalance.objects.all()
    serializer_class = KikobaBalanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['kikoba']


class SavingCycleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Saving Cycles
    """
    queryset = SavingCycle.objects.all()
    serializer_class = SavingCycleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['kikoba', 'is_active']
    ordering_fields = ['start_date']


class LoanProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Loan Products
    """
    queryset = LoanProduct.objects.all()
    serializer_class = LoanProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['kikoba', 'is_active']
    ordering_fields = ['name']


class LoanApplicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Loan Applications
    Supports creating, listing, and retrieving loan applications with file uploads
    """
    queryset = LoanApplication.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'kikoba', 'member']
    ordering_fields = ['application_date']
    
    def get_serializer_class(self):
        """Use different serializer for create action"""
        if self.action == 'create':
            return LoanApplicationCreateSerializer
        return LoanApplicationSerializer
    
    def get_queryset(self):
        """Filter applications for user's vikoba or user's own applications"""
        user = self.request.user
        return LoanApplication.objects.filter(
            Q(member=user) | Q(kikoba__memberships__user=user)
        ).select_related('member', 'kikoba', 'loan_product', 'decision_by').prefetch_related('guarantors').distinct()
    
    def create(self, request, *args, **kwargs):
        """
        Create a new loan application with guarantors
        Supports multipart/form-data for file uploads
        """
        import json
        
        # Handle guarantors as JSON string if sent via form-data
        data = request.data.copy()
        if 'guarantors' in data and isinstance(data['guarantors'], str):
            try:
                data['guarantors'] = json.loads(data['guarantors'])
            except json.JSONDecodeError:
                return Response(
                    {'success': False, 'message': 'Invalid guarantors format', 'errors': {'guarantors': ['Must be valid JSON']}},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = self.get_serializer(data=data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'message': 'Validation failed',
                    'errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        loan_app = serializer.save()
        
        # Return success response with full application details
        response_serializer = LoanApplicationSerializer(loan_app, context={'request': request})
        
        return Response(
            {
                'success': True,
                'message': 'Loan application submitted successfully',
                'data': response_serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    def list(self, request, *args, **kwargs):
        """List loan applications with success wrapper"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve single loan application with success wrapper"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a loan application"""
        from django.utils import timezone
        
        application = self.get_object()
        
        if application.status != 'pending':
            return Response(
                {'success': False, 'message': f'Application is already {application.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.status = 'approved'
        application.decision_by = request.user
        application.decision_date = timezone.now()
        application.remarks = request.data.get('remarks', '')
        application.save()
        
        serializer = self.get_serializer(application)
        return Response({
            'success': True,
            'message': 'Loan application approved successfully',
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a loan application"""
        from django.utils import timezone
        
        application = self.get_object()
        remarks = request.data.get('remarks', '')
        
        if not remarks:
            return Response(
                {'success': False, 'message': 'Validation failed', 'errors': {'remarks': ['Reason for rejection is required']}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if application.status != 'pending':
            return Response(
                {'success': False, 'message': f'Application is already {application.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.status = 'rejected'
        application.decision_by = request.user
        application.decision_date = timezone.now()
        application.remarks = remarks
        application.save()
        
        serializer = self.get_serializer(application)
        return Response({
            'success': True,
            'message': 'Loan application rejected',
            'data': serializer.data
        })


class LoanViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Loans
    """
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['disbursement_date']
    
    def get_queryset(self):
        """Filter loans for user's vikoba"""
        user = self.request.user
        return Loan.objects.filter(
            Q(application__member=user) | Q(application__kikoba__memberships__user=user)
        ).distinct()


class RepaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Loan Repayments
    """
    queryset = Repayment.objects.all()
    serializer_class = RepaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['loan', 'is_verified', 'payment_method']
    ordering_fields = ['payment_date']
    
    def get_queryset(self):
        """Filter repayments for user's loans"""
        user = self.request.user
        return Repayment.objects.filter(
            Q(loan__application__member=user) | 
            Q(loan__application__kikoba__memberships__user=user)
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a repayment"""
        from django.utils import timezone
        
        repayment = self.get_object()
        repayment.is_verified = True
        repayment.verified_by = request.user
        repayment.verified_at = timezone.now()
        repayment.save()
        
        serializer = self.get_serializer(repayment)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Notifications (read-only)
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'is_read']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        """Filter notifications for current user"""
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"detail": "All notifications marked as read"})


class EntryFeePaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Entry Fee Payments
    """
    queryset = EntryFeePayment.objects.all()
    serializer_class = EntryFeePaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['kikoba_membership', 'is_fully_paid']
    
    def get_queryset(self):
        """Filter entry fee payments for user's memberships"""
        user = self.request.user
        return EntryFeePayment.objects.filter(kikoba_membership__user=user)


class ShareContributionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Share Contributions
    """
    queryset = ShareContribution.objects.all()
    serializer_class = ShareContributionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['kikoba_membership', 'is_fully_paid']
    
    def get_queryset(self):
        """Filter share contributions for user's memberships"""
        user = self.request.user
        return ShareContribution.objects.filter(kikoba_membership__user=user)


class EmergencyFundContributionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Emergency Fund Contributions
    """
    queryset = EmergencyFundContribution.objects.all()
    serializer_class = EmergencyFundContributionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['kikoba_membership']
    
    def get_queryset(self):
        """Filter emergency fund contributions for user's memberships"""
        user = self.request.user
        return EmergencyFundContribution.objects.filter(kikoba_membership__user=user)
