"""
Management command to compare how different kikoba types affect member payouts.
This demonstrates the mathematical differences between kikoba models using real data.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from groups.models import Kikoba, KikobaMembership, ShareContribution, EntryFeePayment
from finance import (
    MemberContribution, 
    StandardVikoba, 
    FixedShareVikoba, 
    InterestRefundVikoba,
    RoscaModel
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Compare how different kikoba types calculate member payouts using real data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--kikoba-number',
            type=str,
            help='Kikoba number to analyze (default: uses first kikoba)',
        )

    def handle(self, *args, **options):
        kikoba_number = options.get('kikoba_number')
        
        # Get the kikoba
        if kikoba_number:
            try:
                kikoba = Kikoba.objects.get(kikoba_number=kikoba_number)
            except Kikoba.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Kikoba with number {kikoba_number} not found'))
                return
        else:
            kikoba = Kikoba.objects.first()
            if not kikoba:
                self.stdout.write(self.style.ERROR('No kikoba found in the system'))
                return

        self.stdout.write(self.style.SUCCESS(f'\n{"="*80}'))
        self.stdout.write(self.style.SUCCESS(f'KIKOBA FINANCIAL COMPARISON'))
        self.stdout.write(self.style.SUCCESS(f'{"="*80}'))
        self.stdout.write(f'\nKikoba Name: {kikoba.name}')
        self.stdout.write(f'Kikoba Number: {kikoba.kikoba_number}')
        self.stdout.write(f'Current Type: {kikoba.get_group_type_display()}')
        
        # Get all members
        memberships = KikobaMembership.objects.filter(kikoba=kikoba, is_active=True)
        
        if not memberships.exists():
            self.stdout.write(self.style.WARNING('\nNo active members found in this kikoba'))
            return
            
        self.stdout.write(f'Active Members: {memberships.count()}\n')
        
        # Create sample financial data for demonstration
        self.stdout.write(self.style.WARNING('\n--- SAMPLE SCENARIO FOR DEMONSTRATION ---'))
        self.stdout.write('Assuming each member has:')
        self.stdout.write('  - Contributed shares/savings')
        self.stdout.write('  - Some members have taken loans and paid interest')
        self.stdout.write('  - Some fines have been collected\n')
        
        # Sample data - you can adjust these values
        total_interest_collected = Decimal('50000.00')  # Total interest from all loans
        total_fines_collected = Decimal('10000.00')     # Total fines
        
        # Create sample member contributions
        members = []
        member_data = []
        
        for i, membership in enumerate(memberships):
            # Vary the contributions to make it realistic
            if i == 0:
                shares = Decimal('10')  # 10 shares
                fixed = Decimal('100000')  # 100,000 TZS
                interest = Decimal('15000')  # Paid 15,000 interest
            elif i == 1:
                shares = Decimal('7')
                fixed = Decimal('100000')
                interest = Decimal('10000')
            elif i == 2:
                shares = Decimal('5')
                fixed = Decimal('100000')
                interest = Decimal('8000')
            else:
                shares = Decimal('3')
                fixed = Decimal('100000')
                interest = Decimal('5000')
            
            member_contrib = MemberContribution(
                member_id=membership.user.id,
                shares=shares,
                fixed_contribution=fixed,
                interest_paid=interest,
                fines_paid=Decimal('0')
            )
            members.append(member_contrib)
            member_data.append({
                'name': membership.user.name,
                'phone': membership.user.phone_number,
                'shares': shares,
                'fixed': fixed,
                'interest': interest
            })
        
        # Display member contributions
        self.stdout.write(self.style.SUCCESS(f'\n{"="*80}'))
        self.stdout.write(self.style.SUCCESS('MEMBER CONTRIBUTIONS'))
        self.stdout.write(self.style.SUCCESS(f'{"="*80}'))
        
        for data in member_data:
            self.stdout.write(f"\n{data['name']} ({data['phone']})")
            self.stdout.write(f"  Shares: {data['shares']}")
            self.stdout.write(f"  Fixed Contribution: {data['fixed']:,.2f} TZS")
            self.stdout.write(f"  Interest Paid on Loans: {data['interest']:,.2f} TZS")
        
        total_shares = sum(m.shares for m in members)
        total_fixed = sum(m.fixed_contribution for m in members)
        
        self.stdout.write(f'\n{"-"*80}')
        self.stdout.write(f'Total Shares in Pool: {total_shares}')
        self.stdout.write(f'Total Fixed Contributions: {total_fixed:,.2f} TZS')
        self.stdout.write(f'Total Interest Collected: {total_interest_collected:,.2f} TZS')
        self.stdout.write(f'Total Fines Collected: {total_fines_collected:,.2f} TZS')
        
        # Calculate payouts for each model
        self.stdout.write(self.style.SUCCESS(f'\n\n{"="*80}'))
        self.stdout.write(self.style.SUCCESS('COMPARISON OF KIKOBA TYPES'))
        self.stdout.write(self.style.SUCCESS(f'{"="*80}'))
        
        # 1. Standard VIKOBA (Variable-Share ASCA)
        self.stdout.write(self.style.SUCCESS('\n1. STANDARD VIKOBA (Variable-Share ASCA)'))
        self.stdout.write('-' * 80)
        self.stdout.write('How it works:')
        self.stdout.write('  - Members contribute different amounts (variable shares)')
        self.stdout.write('  - Profits distributed proportionally to shares contributed')
        self.stdout.write('  - More shares = larger payout\n')
        
        standard_payouts = StandardVikoba.calculate_payouts(members, total_interest_collected, total_fines_collected)
        
        for i, data in enumerate(member_data):
            user_id = memberships[i].user.id
            payout = standard_payouts.get(user_id, Decimal('0'))
            shares = data['shares']
            profit = payout - shares
            self.stdout.write(f"{data['name']}: {payout:,.2f} TZS (Shares: {shares}, Profit: {profit:,.2f})")
        
        total_standard = sum(standard_payouts.values())
        self.stdout.write(f'\nTotal Payout: {total_standard:,.2f} TZS')
        
        # 2. Fixed-Share VIKOBA
        self.stdout.write(self.style.SUCCESS('\n\n2. FIXED-SHARE VIKOBA'))
        self.stdout.write('-' * 80)
        self.stdout.write('How it works:')
        self.stdout.write('  - All members contribute the same fixed amount')
        self.stdout.write('  - Profits distributed EQUALLY among all members')
        self.stdout.write('  - Everyone gets the same dividend regardless of contribution\n')
        
        fixed_payouts = FixedShareVikoba.calculate_payouts(members, total_interest_collected, total_fines_collected)
        
        for i, data in enumerate(member_data):
            user_id = memberships[i].user.id
            payout = fixed_payouts.get(user_id, Decimal('0'))
            contribution = data['fixed']
            profit = payout - contribution
            self.stdout.write(f"{data['name']}: {payout:,.2f} TZS (Contribution: {contribution:,.2f}, Profit: {profit:,.2f})")
        
        total_fixed = sum(fixed_payouts.values())
        self.stdout.write(f'\nTotal Payout: {total_fixed:,.2f} TZS')
        
        # 3. Interest Refund VIKOBA
        self.stdout.write(self.style.SUCCESS('\n\n3. INTEREST REFUND VIKOBA'))
        self.stdout.write('-' * 80)
        self.stdout.write('How it works:')
        self.stdout.write('  - Interest paid on loans is REFUNDED to borrowers')
        self.stdout.write('  - Only fines are distributed equally')
        self.stdout.write('  - Borrowers get back their interest + share of fines\n')
        
        interest_payouts = InterestRefundVikoba.calculate_payouts(members, total_interest_collected, total_fines_collected)
        
        for i, data in enumerate(member_data):
            user_id = memberships[i].user.id
            payout = interest_payouts.get(user_id, Decimal('0'))
            contribution = data['fixed']
            interest_refund = data['interest']
            fine_share = total_fines_collected / Decimal(str(len(members)))
            self.stdout.write(f"{data['name']}: {payout:,.2f} TZS")
            self.stdout.write(f"  └─ Contribution: {contribution:,.2f} + Interest Refund: {interest_refund:,.2f} + Fine Share: {fine_share:,.2f}")
        
        total_interest = sum(interest_payouts.values())
        self.stdout.write(f'\nTotal Payout: {total_interest:,.2f} TZS')
        
        # 4. ROSCA Model
        self.stdout.write(self.style.SUCCESS('\n\n4. ROSCA (Rotating Savings and Credit Association)'))
        self.stdout.write('-' * 80)
        self.stdout.write('How it works:')
        self.stdout.write('  - All members contribute the same amount each meeting')
        self.stdout.write('  - Each meeting, one member receives the entire pot')
        self.stdout.write('  - Rotates until everyone has received the pot once\n')
        
        contribution_per_member = Decimal('50000')  # 50,000 TZS per meeting
        pot_size = RoscaModel.calculate_pot_size(float(contribution_per_member), len(members))
        
        self.stdout.write(f"Contribution per member per meeting: {contribution_per_member:,.2f} TZS")
        self.stdout.write(f"Pot size per meeting: {pot_size:,.2f} TZS")
        self.stdout.write(f"Number of meetings needed: {len(members)} (one per member)")
        self.stdout.write(f"\nEach member will receive {pot_size:,.2f} TZS when it's their turn")
        
        # Summary comparison
        self.stdout.write(self.style.SUCCESS(f'\n\n{"="*80}'))
        self.stdout.write(self.style.SUCCESS('SUMMARY: KEY DIFFERENCES'))
        self.stdout.write(self.style.SUCCESS(f'{"="*80}'))
        
        self.stdout.write('\n1. STANDARD VIKOBA:')
        self.stdout.write('   ✓ Encourages higher contributions (more shares = more profit)')
        self.stdout.write('   ✓ Proportional distribution based on investment')
        self.stdout.write('   ✗ May create inequality among members')
        
        self.stdout.write('\n2. FIXED-SHARE VIKOBA:')
        self.stdout.write('   ✓ Equal profit sharing promotes fairness')
        self.stdout.write('   ✓ Simple to understand and manage')
        self.stdout.write('   ✗ No incentive to contribute more')
        
        self.stdout.write('\n3. INTEREST REFUND VIKOBA:')
        self.stdout.write('   ✓ Encourages borrowing (interest is refunded)')
        self.stdout.write('   ✓ Borrowers benefit most from this model')
        self.stdout.write('   ✗ Non-borrowers receive less benefit')
        
        self.stdout.write('\n4. ROSCA:')
        self.stdout.write('   ✓ Very simple and traditional')
        self.stdout.write('   ✓ No interest or complex calculations')
        self.stdout.write('   ✗ No profit generation, just rotation of savings')
        
        self.stdout.write(f'\n{"="*80}\n')
        
        # Show current kikoba type effect
        if kikoba.group_type == 'standard':
            current_effect = f"Members with more shares get proportionally larger payouts"
        elif kikoba.group_type == 'fixed_share':
            current_effect = f"All members receive equal dividends regardless of contribution amount"
        elif kikoba.group_type == 'interest_refund':
            current_effect = f"Borrowers get their interest refunded + equal share of fines"
        elif kikoba.group_type == 'rosca':
            current_effect = f"Each member gets the full pot when it's their turn"
        else:
            current_effect = f"Type not set"
        
        self.stdout.write(self.style.WARNING(f'\nYour current kikoba type: {kikoba.get_group_type_display()}'))
        self.stdout.write(self.style.WARNING(f'Effect on payouts: {current_effect}'))
        self.stdout.write('')
