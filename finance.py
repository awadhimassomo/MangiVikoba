"""
Financial calculations for the VIKOBA application.

This module implements the core financial calculations for different community finance models
including Standard VIKOBA, Fixed-Share VIKOBA, Interest Refund VIKOBA, and ROSCA.
"""
from decimal import Decimal, getcontext
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Set precision for decimal calculations
getcontext().prec = 10

@dataclass
class LoanDetails:
    """Represents a loan with its details."""
    principal: Decimal
    monthly_interest_rate: Decimal
    duration_months: int
    total_interest: Optional[Decimal] = None
    monthly_payment: Optional[Decimal] = None
    total_repayment: Optional[Decimal] = None
    
    def __post_init__(self):
        """Calculate derived loan metrics."""
        self.total_interest = self.principal * self.monthly_interest_rate * self.duration_months
        self.total_repayment = self.principal + self.total_interest
        self.monthly_payment = self.total_repayment / self.duration_months if self.duration_months > 0 else Decimal('0')

@dataclass
class MemberContribution:
    """Represents a member's contribution to the group."""
    member_id: Any
    shares: Decimal = Decimal('0')  # For Standard VIKOBA
    fixed_contribution: Decimal = Decimal('0')  # For Fixed-Share and Interest Refund models
    interest_paid: Decimal = Decimal('0')  # Interest paid on loans
    fines_paid: Decimal = Decimal('0')  # Fines paid
    
    @property
    def total_contribution(self) -> Decimal:
        """Total contribution is either shares or fixed contribution, whichever is applicable."""
        return self.shares if self.shares else self.fixed_contribution

class VikobaCalculator:
    """Base class for VIKOBA financial calculations."""
    
    @staticmethod
    def calculate_loan(principal: float, annual_interest_rate: float, duration_months: int) -> LoanDetails:
        """
        Calculate loan details using simple interest.
        
        Args:
            principal: Loan amount
            annual_interest_rate: Annual interest rate as a decimal (e.g., 0.10 for 10%)
            duration_months: Loan duration in months
            
        Returns:
            LoanDetails object with calculated values
        """
        monthly_rate = Decimal(str(annual_interest_rate)) / Decimal('12')
        return LoanDetails(
            principal=Decimal(str(principal)),
            monthly_interest_rate=monthly_rate,
            duration_months=duration_months
        )

class StandardVikoba(VikobaCalculator):
    """Standard VIKOBA / Variable-Share ASCA model."""
    
    @classmethod
    def calculate_payouts(
        cls,
        members: List[MemberContribution],
        total_interest: Decimal,
        total_fines: Decimal
    ) -> Dict[Any, Decimal]:
        """
        Calculate payouts for members based on their shares.
        
        Args:
            members: List of member contributions
            total_interest: Total interest collected from all loans
            total_fines: Total fines collected
            
        Returns:
            Dictionary mapping member_id to payout amount
        """
        total_shares = sum(m.shares for m in members)
        if total_shares == 0:
            return {}
            
        total_profit = total_interest + total_fines
        profit_per_share = total_profit / total_shares
        
        return {
            m.member_id: m.shares * (Decimal('1') + profit_per_share)
            for m in members
        }

class FixedShareVikoba(VikobaCalculator):
    """Fixed-Share VIKOBA model with equal profit sharing."""
    
    @classmethod
    def calculate_payouts(
        cls,
        members: List[MemberContribution],
        total_interest: Decimal,
        total_fines: Decimal
    ) -> Dict[Any, Decimal]:
        """
        Calculate equal payouts for all members.
        
        Args:
            members: List of member contributions
            total_interest: Total interest collected from all loans
            total_fines: Total fines collected
            
        Returns:
            Dictionary mapping member_id to payout amount
        """
        if not members:
            return {}
            
        total_profit = total_interest + total_fines
        equal_dividend = total_profit / Decimal(str(len(members)))
        
        return {
            m.member_id: m.fixed_contribution + equal_dividend
            for m in members
        }

class InterestRefundVikoba(VikobaCalculator):
    """Interest Refund VIKOBA model where interest is refunded to borrowers."""
    
    @classmethod
    def calculate_payouts(
        cls,
        members: List[MemberContribution],
        total_interest: Decimal,  # Unused in this model
        total_fines: Decimal
    ) -> Dict[Any, Decimal]:
        """
        Calculate payouts with interest refund and equal sharing of fines.
        
        Args:
            members: List of member contributions with interest paid
            total_interest: Total interest collected (for reference)
            total_fines: Total fines collected
            
        Returns:
            Dictionary mapping member_id to payout amount
        """
        if not members:
            return {}
            
        fine_share = total_fines / Decimal(str(len(members)))
        
        return {
            m.member_id: m.fixed_contribution + m.interest_paid + fine_share
            for m in members
        }

class RoscaModel:
    """Rotating Savings and Credit Association (ROSCA) model."""
    
    @staticmethod
    def calculate_pot_size(contribution: float, num_members: int) -> float:
        """
        Calculate the pot size for each meeting.
        
        Args:
            contribution: Fixed contribution per member per meeting
            num_members: Total number of members
            
        Returns:
            Pot size (total contribution per meeting)
        """
        return contribution * num_members
    
    @staticmethod
    def calculate_payout_schedule(
        contribution: float,
        num_members: int,
        meeting_frequency: str = 'monthly'
    ) -> List[Dict[str, Any]]:
        """
        Generate a payout schedule for the ROSCA.
        
        Args:
            contribution: Fixed contribution per member per meeting
            num_members: Total number of members
            meeting_frequency: 'weekly', 'biweekly', or 'monthly'
            
        Returns:
            List of dictionaries containing meeting details
        """
        pot_size = contribution * num_members
        schedule = []
        
        for i in range(num_members):
            schedule.append({
                'meeting_number': i + 1,
                'pot_size': float(pot_size),
                'recipient': f"Member {i + 1}",  # In practice, this would be determined by the group
                'contributions': {
                    f"Member {j + 1}": float(contribution)
                    for j in range(num_members)
                }
            })
            
        return schedule

# Example usage
if __name__ == "__main__":
    # Example 1: Standard VIKOBA
    print("=== Standard VIKOBA Example ===")
    members = [
        MemberContribution(member_id=1, shares=Decimal('5')),
        MemberContribution(member_id=2, shares=Decimal('3')),
        MemberContribution(member_id=3, shares=Decimal('2'))
    ]
    total_interest = Decimal('1000')
    total_fines = Decimal('200')
    
    payouts = StandardVikoba.calculate_payouts(members, total_interest, total_fines)
    for member_id, payout in payouts.items():
        print(f"Member {member_id} payout: {payout:.2f}")
    
    # Example 2: Loan calculation
    print("\n=== Loan Calculation Example ===")
    loan = VikobaCalculator.calculate_loan(10000, 0.10, 12)  # 10% annual interest, 12 months
    print(f"Principal: {loan.principal}")
    print(f"Monthly Payment: {loan.monthly_payment:.2f}")
    print(f"Total Interest: {loan.total_interest:.2f}")
    print(f"Total Repayment: {loan.total_repayment:.2f}")
