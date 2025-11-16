""
Unit tests for financial calculations in the VIKOBA application.
"""
import unittest
from decimal import Decimal
from finance import (
    LoanDetails, MemberContribution, VikobaCalculator,
    StandardVikoba, FixedShareVikoba, InterestRefundVikoba, RoscaModel
)

class TestLoanDetails(unittest.TestCase):
    """Test LoanDetails class and basic loan calculations."""
    
    def test_loan_calculation(self):
        ""Test basic loan calculation with simple interest."""
        # 10,000 TZS at 10% annual interest for 1 year (12 months)
        loan = LoanDetails(
            principal=Decimal('10000'),
            monthly_interest_rate=Decimal('0.10') / 12,  # Monthly rate
            duration_months=12
        )
        
        # Expected calculations
        expected_interest = Decimal('10000') * Decimal('0.10')  # 10% of principal
        expected_total = Decimal('10000') + expected_interest
        expected_monthly = expected_total / 12
        
        self.assertAlmostEqual(loan.total_interest, expected_interest, places=2)
        self.assertAlmostEqual(loan.total_repayment, expected_total, places=2)
        self.assertAlmostEqual(loan.monthly_payment, expected_monthly, places=2)
    
    def test_zero_interest_loan(self):
        ""Test loan with zero interest."""
        loan = LoanDetails(
            principal=Decimal('10000'),
            monthly_interest_rate=Decimal('0'),
            duration_months=12
        )
        
        self.assertEqual(loan.total_interest, Decimal('0'))
        self.assertEqual(loan.total_repayment, Decimal('10000'))
        self.assertAlmostEqual(loan.monthly_payment, Decimal('10000')/12, places=2)

class TestVikobaCalculator(unittest.TestCase):
    ""Test the base VikobaCalculator class."""
    
    def test_calculate_loan(self):
        ""Test the static method for loan calculation."""
        # 100,000 TZS at 12% annual interest for 6 months
        loan = VikobaCalculator.calculate_loan(
            principal=100000,
            annual_interest_rate=0.12,
            duration_months=6
        )
        
        # Expected: 100,000 * 12% * (6/12) = 6,000 interest
        expected_interest = Decimal('6000')
        expected_total = Decimal('106000')
        
        self.assertIsInstance(loan, LoanDetails)
        self.assertAlmostEqual(loan.total_interest, expected_interest, places=2)
        self.assertAlmostEqual(loan.total_repayment, expected_total, places=2)
        self.assertAlmostEqual(loan.monthly_payment, expected_total/6, places=2)

class TestStandardVikoba(unittest.TestCase):
    ""Test Standard VIKOBA / Variable-Share ASCA model."""
    
    def test_profit_distribution(self):
        ""Test profit distribution based on shares."""
        members = [
            MemberContribution(member_id=1, shares=Decimal('5')),  # 50%
            MemberContribution(member_id=2, shares=Decimal('3')),  # 30%
            MemberContribution(member_id=3, shares=Decimal('2'))   # 20%
        ]
        total_interest = Decimal('10000')
        total_fines = Decimal('2000')
        
        payouts = StandardVikoba.calculate_payouts(members, total_interest, total_fines)
        
        # Total profit = 10,000 + 2,000 = 12,000
        # Profit per share = 12,000 / (5+3+2) = 1,200
        expected_payouts = {
            1: Decimal('5') * (1 + Decimal('1200')/Decimal('100')),  # 5 * 13 = 65
            2: Decimal('3') * (1 + Decimal('1200')/Decimal('100')),  # 3 * 13 = 39
            3: Decimal('2') * (1 + Decimal('1200')/Decimal('100'))   # 2 * 13 = 26
        }
        
        for member_id, expected in expected_payouts.items():
            self.assertAlmostEqual(payouts[member_id], expected, places=2)
    
    def test_no_shares(self):
        ""Test behavior when no shares are present."""
        members = []
        result = StandardVikoba.calculate_payouts(members, Decimal('1000'), Decimal('200'))
        self.assertEqual(result, {})

class TestFixedShareVikoba(unittest.TestCase):
    ""Test Fixed-Share VIKOBA model."""
    
    def test_equal_distribution(self):
        ""Test equal distribution of profits."""
        members = [
            MemberContribution(member_id=1, fixed_contribution=Decimal('1000')),
            MemberContribution(member_id=2, fixed_contribution=Decimal('1000')),
            MemberContribution(member_id=3, fixed_contribution=Decimal('1000'))
        ]
        total_interest = Decimal('9000')
        total_fines = Decimal('3000')
        
        payouts = FixedShareVikoba.calculate_payouts(members, total_interest, total_fines)
        
        # Each member should get 1/3 of total profit (12,000 / 3 = 4,000)
        # Plus their original contribution (1,000) = 5,000
        expected_payout = Decimal('1000') + (total_interest + total_fines) / 3
        
        for payout in payouts.values():
            self.assertAlmostEqual(payout, expected_payout, places=2)
    
    def test_varying_contributions(self):
        ""Test with varying fixed contributions."""
        members = [
            MemberContribution(member_id=1, fixed_contribution=Decimal('2000')),
            MemberContribution(member_id=2, fixed_contribution=Decimal('1000'))
        ]
        payouts = FixedShareVikoba.calculate_payouts(members, Decimal('600'), Decimal('0'))
        
        # Each gets equal share of profit (600 / 2 = 300) plus their contribution
        self.assertAlmostEqual(payouts[1], Decimal('2300'), places=2)  # 2000 + 300
        self.assertAlmostEqual(payouts[2], Decimal('1300'), places=2)  # 1000 + 300

class TestInterestRefundVikoba(unittest.TestCase):
    ""Test Interest Refund VIKOBA model."""
    
    def test_interest_refund(self):
        ""Test interest refund and fine distribution."""
        members = [
            MemberContribution(
                member_id=1,
                fixed_contribution=Decimal('1000'),
                interest_paid=Decimal('1500'),  # Will be refunded
                fines_paid=Decimal('200')
            ),
            MemberContribution(
                member_id=2,
                fixed_contribution=Decimal('1000'),
                interest_paid=Decimal('500'),  # Will be refunded
                fines_paid=Decimal('100')
            )
        ]
        total_interest = Decimal('2000')  # 1500 + 500
        total_fines = Decimal('300')      # 200 + 100
        
        payouts = InterestRefundVikoba.calculate_payouts(
            members, total_interest, total_fines
        )
        
        # Each gets their contribution + interest paid + equal share of fines
        # Fine share = 300 / 2 = 150 each
        self.assertAlmostEqual(
            payouts[1],
            Decimal('1000') + Decimal('1500') + Decimal('150'),  # 1000 + 1500 + 150
            places=2
        )
        self.assertAlmostEqual(
            payouts[2],
            Decimal('1000') + Decimal('500') + Decimal('150'),  # 1000 + 500 + 150
            places=2
        )

class TestRoscaModel(unittest.TestCase):
    ""Test ROSCA (Rotating Savings and Credit Association) model."""
    
    def test_pot_size_calculation(self):
        ""Test pot size calculation."""
        pot_size = RoscaModel.calculate_pot_size(10000, 10)  # 10 members, 10,000 each
        self.assertEqual(pot_size, 100000)  # 10 * 10,000 = 100,000
    
    def test_payout_schedule(self):
        ""Test generation of payout schedule."""
        schedule = RoscaModel.calculate_payout_schedule(10000, 3)
        
        self.assertEqual(len(schedule), 3)  # 3 meetings
        self.assertEqual(schedule[0]['pot_size'], 30000)  # 3 * 10,000
        self.assertEqual(len(schedule[0]['contributions']), 3)  # 3 members
        
        # Check each member's contribution in the first meeting
        for contribution in schedule[0]['contributions'].values():
            self.assertEqual(contribution, 10000)

if __name__ == '__main__':
    unittest.main()
