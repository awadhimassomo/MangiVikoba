"""
Simple test for the my_total endpoint
"""
import requests

BASE_URL = "http://192.168.1.101:8000"

print("="*80)
print("TESTING MY_TOTAL ENDPOINT")
print("="*80)

# Step 1: Login
print("\n1. Logging in...")
login_response = requests.post(
    f"{BASE_URL}/api/v1/auth/token/",
    json={
        "phone_number": "+255742178726",
        "password": "4466"
    }
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

tokens = login_response.json()
access_token = tokens['access']
print(f"✅ Login successful!")
print(f"Token: {access_token[:30]}...")

# Step 2: Call my_total endpoint
print("\n2. Calling my_total endpoint...")
print(f"URL: {BASE_URL}/api/v1/vikoba/1/my_total/")

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

print(f"Headers: {headers}")

response = requests.get(
    f"{BASE_URL}/api/v1/vikoba/1/my_total/",
    headers=headers
)

print(f"\n3. Response:")
print(f"Status Code: {response.status_code}")
print(f"Response Body:")
print(response.text)

if response.status_code == 200:
    data = response.json()
    print("\n✅ SUCCESS!")
    print("="*80)
    print(f"Kikoba: {data['kikoba']['name']}")
    print(f"User: {data['user']['name']}")
    print(f"Total Payout: {data['financial_data']['total_payout']:,.2f} TZS")
    print(f"Profit: {data['financial_data']['profit']:,.2f} TZS")
    print("="*80)
else:
    print(f"\n❌ FAILED with status {response.status_code}")
    print("="*80)
