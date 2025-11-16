"""
Test script for the member totals API endpoint
"""
import requests
import json

# Configuration
BASE_URL = "http://192.168.1.101:8000"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/token/"  # API v1 prefix
MEMBER_TOTALS_URL = f"{BASE_URL}/api/v1/vikoba/1/member_totals/"  # API v1 prefix + vikoba

# Test credentials (use actual credentials from your system)
PHONE_NUMBER = "+255742178726"  # Replace with actual phone number
PIN = "1234"  # Replace with actual PIN

def test_member_totals_endpoint():
    """Test the member totals API endpoint"""
    
    print("=" * 80)
    print("TESTING MEMBER TOTALS API ENDPOINT")
    print("=" * 80)
    
    # Step 1: Login to get JWT token
    print("\n1. Logging in...")
    login_data = {
        "phone_number": PHONE_NUMBER,
        "password": PIN
    }
    
    try:
        response = requests.post(LOGIN_URL, json=login_data)
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens.get('access')
            print("✅ Login successful!")
            print(f"Access Token: {access_token[:50]}...")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return
    
    # Step 2: Call member totals endpoint
    print("\n2. Fetching member totals...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(MEMBER_TOTALS_URL, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Member totals retrieved successfully!")
            print("\n" + "=" * 80)
            print("RESPONSE DATA")
            print("=" * 80)
            print(json.dumps(data, indent=2))
            
            # Display formatted summary
            print("\n" + "=" * 80)
            print("FORMATTED SUMMARY")
            print("=" * 80)
            print(f"\nKikoba: {data['kikoba']['name']} ({data['kikoba']['kikoba_number']})")
            print(f"Type: {data['kikoba']['group_type_display']}")
            print(f"\nCalculation Method: {data['financial_summary']['calculation_method']}")
            print(f"\nTotal Interest Collected: {data['financial_summary']['total_interest_collected']:,.2f} TZS")
            print(f"Total Fines Collected: {data['financial_summary']['total_fines_collected']:,.2f} TZS")
            print(f"Total Profit: {data['financial_summary']['total_profit']:,.2f} TZS")
            
            print(f"\n--- MEMBER PAYOUTS ---")
            for member in data['members']:
                print(f"\n{member['name']} ({member['phone_number']})")
                print(f"  Contribution: {member['contribution']:,.2f} TZS")
                print(f"  Interest Paid: {member['interest_paid']:,.2f} TZS")
                print(f"  Total Payout: {member['total_payout']:,.2f} TZS")
                print(f"  Profit: {member['profit']:,.2f} TZS")
            
            print(f"\n--- OVERALL SUMMARY ---")
            print(f"Total Members: {data['summary']['total_members']}")
            print(f"Total Contributions: {data['summary']['total_contributions']:,.2f} TZS")
            print(f"Total Payouts: {data['summary']['total_payouts']:,.2f} TZS")
            print(f"Total Profit Distributed: {data['summary']['total_profit_distributed']:,.2f} TZS")
            
        else:
            print(f"❌ Failed to fetch member totals: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error fetching member totals: {e}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_member_totals_endpoint()
