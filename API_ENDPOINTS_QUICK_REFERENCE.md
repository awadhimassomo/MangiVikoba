# 🚀 API Endpoints Quick Reference

## Base URL
```
http://192.168.1.101:8000
```

---

## 🔐 Authentication

### Login (Get JWT Token)
```http
POST /api/v1/auth/token/
```

**Request:**
```json
{
  "phone_number": "+255712345678",
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

**Use the `access` token in all subsequent requests:**
```
Authorization: Bearer {access_token}
```

---

## 💰 Member Totals Endpoints

### ⭐ Get My Total (User-Specific)
**Recommended for Mobile Apps**

```http
GET /api/v1/vikoba/{kikoba_id}/my_total/
```

**Full URL:**
```
http://192.168.1.101:8000/api/v1/vikoba/1/my_total/
```

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**What it returns:**
- Your contribution in this kikoba
- Your total payout
- Your profit
- Kikoba financial summary

**Example Response:**
```json
{
  "kikoba": {
    "id": 1,
    "name": "Wanumeishuu",
    "kikoba_number": "KB000001"
  },
  "user": {
    "id": 5,
    "name": "John Doe",
    "phone_number": "+255712345678"
  },
  "financial_data": {
    "contribution": 100000.00,
    "shares": 10.0,
    "interest_paid_on_loans": 15000.00,
    "total_payout": 115000.00,
    "profit": 15000.00
  },
  "message": "Your total payout in Wanumeishuu is 115,000.00 TZS (Profit: 15,000.00 TZS)"
}
```

---

### 📊 Get All Member Totals (Admin View)

```http
GET /api/v1/vikoba/{kikoba_id}/member_totals/
```

**Full URL:**
```
http://192.168.1.101:8000/api/v1/vikoba/1/member_totals/
```

**What it returns:**
- All members' contributions and payouts
- Financial summary for the kikoba
- Overall totals

---

## 👥 User Endpoints

### Get My Profile
```http
GET /api/v1/users/me/
```

### Get My Vikobas
```http
GET /api/v1/users/me/my_vikoba/
```

**Returns:** List of all vikobas you're a member of

---

## 📝 Vikoba Endpoints

### List All Vikobas
```http
GET /api/v1/vikoba/
```

### Get Specific Vikoba
```http
GET /api/v1/vikoba/{id}/
```

### Get Vikoba Members
```http
GET /api/v1/vikoba/{id}/members/
```

### Get Vikoba Balance
```http
GET /api/v1/vikoba/{id}/balance/
```

---

## 🔢 Complete URL Examples

### For Wanumeishuu (KB000001) - Kikoba ID: 1

1. **Get my total:**
   ```
   GET http://192.168.1.101:8000/api/v1/vikoba/1/my_total/
   ```

2. **Get all member totals:**
   ```
   GET http://192.168.1.101:8000/api/v1/vikoba/1/member_totals/
   ```

3. **Get kikoba details:**
   ```
   GET http://192.168.1.101:8000/api/v1/vikoba/1/
   ```

4. **Get kikoba members:**
   ```
   GET http://192.168.1.101:8000/api/v1/vikoba/1/members/
   ```

---

## 🧪 Testing with cURL

### 1. Login
```bash
curl -X POST http://192.168.1.101:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+255742178726", "password": "1234"}'
```

### 2. Get My Total (replace TOKEN)
```bash
curl -X GET http://192.168.1.101:8000/api/v1/vikoba/1/my_total/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json"
```

### 3. Get All Member Totals (replace TOKEN)
```bash
curl -X GET http://192.168.1.101:8000/api/v1/vikoba/1/member_totals/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json"
```

---

## 📱 JavaScript/React Native Example

```javascript
// Login
const login = async () => {
  const response = await fetch('http://192.168.1.101:8000/api/v1/auth/token/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      phone_number: '+255712345678',
      password: '1234'
    })
  });
  const data = await response.json();
  return data.access;
};

// Get My Total
const getMyTotal = async (kikobaId, token) => {
  const response = await fetch(
    `http://192.168.1.101:8000/api/v1/vikoba/${kikobaId}/my_total/`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  return await response.json();
};

// Usage
const token = await login();
const myTotal = await getMyTotal(1, token);
console.log(myTotal.financial_data.total_payout); // Your payout amount
```

---

## ⚠️ Important Notes

1. **URL Prefix:** Use `/api/vikoba/` **NOT** `/api/kikoba/`
2. **Authentication:** All endpoints require JWT token except `/api/token/`
3. **Kikoba ID:** Use the numeric ID (e.g., 1, 2, 3), not the kikoba number (KB000001)
4. **Server Address:** Update `192.168.1.101` to your actual server IP if different

---

## 🔍 Finding Your Kikoba ID

If you have the kikoba number (e.g., KB000001), you can find the ID:

```http
GET /api/v1/vikoba/?search=KB000001
```

Or list all your vikobas:
```http
GET /api/v1/users/me/my_vikoba/
```

---

## ❓ Troubleshooting

### Error: 404 Not Found
- ✅ Check URL: Should be `/api/v1/vikoba/` not `/api/vikoba/` or `/api/kikoba/`
- ✅ Verify kikoba ID exists
- ✅ Ensure server is running
- ✅ Include the `/api/v1/` prefix

### Error: 401 Unauthorized
- ✅ Check JWT token is valid
- ✅ Include Authorization header
- ✅ Token might be expired - login again

### Error: "You are not a member of this kikoba"
- ✅ Verify you're a member of the kikoba you're querying
- ✅ Check if membership is active

---

## 📞 Support

Server running at: `http://192.168.1.101:8000`

To check if server is running:
```bash
curl http://192.168.1.101:8000/api/v1/
```
