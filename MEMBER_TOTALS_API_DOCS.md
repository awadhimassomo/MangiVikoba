# Member Totals API Documentation

## Overview
This API endpoint calculates and returns member totals/payouts based on the kikoba type. It demonstrates how different kikoba types (Standard VIKOBA, Fixed-Share VIKOBA, Interest Refund VIKOBA, ROSCA) affect member payouts.

---

## Endpoint Details

### URL
```
GET /api/kikoba/{kikoba_id}/member_totals/
```

### Base URL
```
http://192.168.1.101:8000
```

### Full Endpoint Example
```
http://192.168.1.101:8000/api/kikoba/1/member_totals/
```

---

## Authentication
This endpoint requires JWT authentication.

### Headers Required
```http
Authorization: Bearer {your_jwt_token}
Content-Type: application/json
```

### Getting JWT Token
First, login to get the access token:

**Endpoint:** `POST /api/token/`

**Request Body:**
```json
{
    "phone_number": "+255742178726",
    "password": "1234"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

Use the `access` token in the Authorization header.

---

## Request Examples

### cURL Example
```bash
# Step 1: Login
curl -X POST http://192.168.1.101:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+255742178726",
    "password": "1234"
  }'

# Step 2: Get member totals (replace TOKEN with actual token)
curl -X GET http://192.168.1.101:8000/api/kikoba/1/member_totals/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json"
```

### JavaScript/React Native Example
```javascript
// Step 1: Login
const login = async () => {
  const response = await fetch('http://192.168.1.101:8000/api/token/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      phone_number: '+255742178726',
      password: '1234',
    }),
  });
  
  const data = await response.json();
  return data.access; // JWT token
};

// Step 2: Get member totals
const getMemberTotals = async (kikobaId, token) => {
  const response = await fetch(
    `http://192.168.1.101:8000/api/kikoba/${kikobaId}/member_totals/`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );
  
  const data = await response.json();
  return data;
};

// Usage
const token = await login();
const memberTotals = await getMemberTotals(1, token);
console.log(memberTotals);
```

### Python Example
```python
import requests

# Step 1: Login
login_url = "http://192.168.1.101:8000/api/token/"
login_data = {
    "phone_number": "+255742178726",
    "password": "1234"
}
response = requests.post(login_url, json=login_data)
token = response.json()['access']

# Step 2: Get member totals
totals_url = "http://192.168.1.101:8000/api/kikoba/1/member_totals/"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
response = requests.get(totals_url, headers=headers)
data = response.json()
print(data)
```

---

## Response Format

### Success Response (200 OK)

```json
{
    "kikoba": {
        "id": 1,
        "name": "Wanumeishuu",
        "kikoba_number": "KB000001",
        "group_type": "interest_refund",
        "group_type_display": "Interest Refund VIKOBA"
    },
    "financial_summary": {
        "total_interest_collected": 50000.00,
        "total_fines_collected": 5000.00,
        "total_profit": 55000.00,
        "calculation_method": "Interest refunded to borrowers + equal share of fines"
    },
    "members": [
        {
            "user_id": 1,
            "name": "John Doe",
            "phone_number": "+255712345678",
            "contribution": 100000.00,
            "shares": 10.0,
            "interest_paid": 15000.00,
            "total_payout": 115000.00,
            "profit": 15000.00
        },
        {
            "user_id": 2,
            "name": "Jane Smith",
            "phone_number": "+255712345679",
            "contribution": 100000.00,
            "shares": 7.0,
            "interest_paid": 10000.00,
            "total_payout": 110000.00,
            "profit": 10000.00
        }
    ],
    "summary": {
        "total_members": 2,
        "total_contributions": 200000.00,
        "total_payouts": 225000.00,
        "total_profit_distributed": 25000.00
    }
}
```

### Response Fields Explanation

#### `kikoba` Object
- `id`: Kikoba database ID
- `name`: Kikoba name
- `kikoba_number`: Unique kikoba identifier (e.g., KB000001)
- `group_type`: Kikoba type code (standard, fixed_share, interest_refund, rosca)
- `group_type_display`: Human-readable kikoba type

#### `financial_summary` Object
- `total_interest_collected`: Total interest from all loans (TZS)
- `total_fines_collected`: Total fines collected (TZS)
- `total_profit`: Sum of interest + fines (TZS)
- `calculation_method`: Description of how payouts are calculated

#### `members` Array
Each member object contains:
- `user_id`: User database ID
- `name`: Member full name
- `phone_number`: Member phone number
- `contribution`: Total amount contributed (shares + fees + emergency fund)
- `shares`: Number of shares (for standard VIKOBA)
- `interest_paid`: Interest paid on loans by this member
- `total_payout`: Total amount member will receive
- `profit`: Profit earned (total_payout - contribution)

#### `summary` Object
- `total_members`: Number of active members
- `total_contributions`: Sum of all member contributions
- `total_payouts`: Sum of all member payouts
- `total_profit_distributed`: Total profit distributed to members

---

## How Kikoba Types Affect Calculations

### 1. Standard VIKOBA (Variable-Share ASCA)
**Calculation Method:** Proportional to shares

- Members can contribute different amounts
- More shares = more profit
- Formula: `payout = shares × (1 + profit_per_share)`
- Encourages higher contributions

**Example:**
- Member A: 10 shares → Gets larger share of profit
- Member B: 5 shares → Gets smaller share of profit

### 2. Fixed-Share VIKOBA
**Calculation Method:** Equal distribution

- All members contribute the same fixed amount
- Profits divided equally among all members
- Formula: `payout = contribution + (total_profit / number_of_members)`
- Fair and simple

**Example:**
- Member A: 100,000 TZS → Gets equal dividend
- Member B: 100,000 TZS → Gets equal dividend

### 3. Interest Refund VIKOBA ✅ (Current for Wanumeishuu)
**Calculation Method:** Interest refunded to borrowers + equal share of fines

- Interest paid on loans is refunded to borrowers
- Fines are distributed equally
- Formula: `payout = contribution + interest_paid + (fines / number_of_members)`
- Encourages borrowing

**Example:**
- Borrower: Gets back their interest + share of fines
- Non-borrower: Gets only share of fines

### 4. ROSCA (Rotating Savings)
**Calculation Method:** Rotating pot

- Each meeting, one member receives the entire pot
- No interest or profit distribution
- Formula: `pot_size = contribution_per_member × number_of_members`
- Simple traditional model

---

## Error Responses

### 404 Not Found
```json
{
    "detail": "No active members in this kikoba"
}
```
**Cause:** Kikoba has no active members

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```
**Cause:** Missing or invalid JWT token

### 403 Forbidden
```json
{
    "detail": "You do not have permission to perform this action."
}
```
**Cause:** User doesn't have access to this kikoba

---

## Testing

### Using the Test Script
Run the included test script:
```bash
python test_member_totals_api.py
```

Make sure to update the credentials in the script:
```python
PHONE_NUMBER = "+255742178726"  # Your phone number
PIN = "1234"  # Your PIN
```

### Using Postman
1. Import the `MangiVikoba_API.postman_collection.json`
2. Add a new request: `GET /api/kikoba/1/member_totals/`
3. Set Authorization to Bearer Token
4. Add your JWT token
5. Send request

---

## Mobile App Integration Tips

### 1. Display Member Totals
```javascript
const MemberTotals = ({ kikobaId }) => {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    fetchMemberTotals();
  }, [kikobaId]);
  
  const fetchMemberTotals = async () => {
    const token = await getStoredToken();
    const response = await fetch(
      `${API_BASE_URL}/api/kikoba/${kikobaId}/member_totals/`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    const data = await response.json();
    setData(data);
  };
  
  return (
    <View>
      <Text>{data?.kikoba.name}</Text>
      <Text>Type: {data?.kikoba.group_type_display}</Text>
      <Text>Total Profit: {data?.financial_summary.total_profit} TZS</Text>
      
      {data?.members.map(member => (
        <View key={member.user_id}>
          <Text>{member.name}</Text>
          <Text>Payout: {member.total_payout} TZS</Text>
          <Text>Profit: {member.profit} TZS</Text>
        </View>
      ))}
    </View>
  );
};
```

### 2. Cache the Response
```javascript
import AsyncStorage from '@react-native-async-storage/async-storage';

// Cache the data
await AsyncStorage.setItem(
  `member_totals_${kikobaId}`,
  JSON.stringify(data)
);

// Retrieve cached data
const cached = await AsyncStorage.getItem(`member_totals_${kikobaId}`);
if (cached) {
  setData(JSON.parse(cached));
}
```

### 3. Handle Loading States
```javascript
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

try {
  setLoading(true);
  const data = await getMemberTotals(kikobaId, token);
  setData(data);
} catch (err) {
  setError(err.message);
} finally {
  setLoading(false);
}
```

---

## Support

For questions or issues:
- Check that the Django server is running: `python manage.py runserver`
- Verify JWT token is valid
- Ensure kikoba ID exists in the database
- Check network connectivity to `http://192.168.1.101:8000`

---

## Changelog

### Version 1.0 (November 16, 2025)
- Initial release
- Support for all 4 kikoba types
- Real-time calculation based on database data
- Aggregates contributions, interest, and fines
