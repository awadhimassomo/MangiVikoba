"""
Simple API Test Script
This script tests the basic functionality of the MangiVikoba REST API
"""

import requests
import json

# Configuration
BASE_URL = "http://192.168.1.197:8000/api/v1"
TEST_USER = {
    "phone_number": "0700000001",
    "name": "API Test User",
    "email": "apitest@example.com",
    "password": "TestPassword123!",
    "password_confirm": "TestPassword123!",
    "role": "member"
}

def print_response(response, title):
    """Print formatted API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*60}\n")

def test_api():
    """Run basic API tests"""
    
    print("Starting API Tests...")
    
    # Test 1: Register new user
    print("\n1. Testing User Registration...")
    response = requests.post(f"{BASE_URL}/users/", json=TEST_USER)
    print_response(response, "User Registration")
    
    if response.status_code != 201:
        print("⚠️  User registration failed. User might already exist.")
    
    # Test 2: Login
    print("\n2. Testing Login (Get JWT Token)...")
    login_data = {
        "phone_number": TEST_USER["phone_number"],
        "password": TEST_USER["password"]
    }
    response = requests.post(f"{BASE_URL}/auth/token/", json=login_data)
    print_response(response, "Login")
    
    if response.status_code != 200:
        print("❌ Login failed. Cannot continue with tests.")
        return
    
    token_data = response.json()
    access_token = token_data.get("access")
    
    # Set authorization header for subsequent requests
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test 3: Get current user profile
    print("\n3. Testing Get Current User Profile...")
    response = requests.get(f"{BASE_URL}/users/me/", headers=headers)
    print_response(response, "Current User Profile")
    
    # Test 4: List Vikoba
    print("\n4. Testing List Vikoba...")
    response = requests.get(f"{BASE_URL}/vikoba/", headers=headers)
    print_response(response, "List Vikoba")
    
    # Test 5: Create Kikoba
    print("\n5. Testing Create Kikoba...")
    kikoba_data = {
        "name": f"Test Kikoba API {token_data.get('access')[:8]}",
        "description": "Test kikoba created via API",
        "contribution_frequency": "monthly",
        "interest_rate": "5.00",
        "loan_limit_factor": "3.00",
        "loan_term_days": 90,
        "late_payment_penalty": "1.00",
        "is_center_kikoba": True,
        "location": "Test Location",
        "estimated_members": "11-20"
    }
    response = requests.post(f"{BASE_URL}/vikoba/", json=kikoba_data, headers=headers)
    print_response(response, "Create Kikoba")
    
    if response.status_code == 201:
        kikoba_id = response.json().get("id")
        
        # Test 6: Get Kikoba Details
        print("\n6. Testing Get Kikoba Details...")
        response = requests.get(f"{BASE_URL}/vikoba/{kikoba_id}/", headers=headers)
        print_response(response, "Kikoba Details")
        
        # Test 7: Get Kikoba Members
        print("\n7. Testing Get Kikoba Members...")
        response = requests.get(f"{BASE_URL}/vikoba/{kikoba_id}/members/", headers=headers)
        print_response(response, "Kikoba Members")
    
    # Test 8: Get User's Vikoba
    print("\n8. Testing Get User's Vikoba...")
    response = requests.get(f"{BASE_URL}/users/my_vikoba/", headers=headers)
    print_response(response, "User's Vikoba")
    
    # Test 9: List Notifications
    print("\n9. Testing List Notifications...")
    response = requests.get(f"{BASE_URL}/notifications/", headers=headers)
    print_response(response, "Notifications")
    
    # Test 10: Token Refresh
    print("\n10. Testing Token Refresh...")
    refresh_data = {"refresh": token_data.get("refresh")}
    response = requests.post(f"{BASE_URL}/auth/token/refresh/", json=refresh_data)
    print_response(response, "Token Refresh")
    
    print("\n✅ API Tests Completed!")
    print("\nNOTE: Some tests may fail if test data already exists in the database.")

if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to the API server.")
        print("Please make sure the Django server is running at http://192.168.1.197:8000")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
