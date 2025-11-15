import requests
import json

# Test the login endpoint
url = "http://192.168.1.197:8000/api/v1/auth/token/"

# Test data - replace with actual phone number and password
test_data = {
    "phone_number": "+255712345678",  # Replace with actual phone number
    "password": "testpassword123"      # Replace with actual password
}

print("Testing login endpoint...")
print(f"URL: {url}")
print(f"Request Data: {json.dumps(test_data, indent=2)}")
print("-" * 50)

try:
    response = requests.post(url, json=test_data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print("-" * 50)
    print(f"Response Body:")
    
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")
