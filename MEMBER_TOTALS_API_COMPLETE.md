# Complete Member Totals API Documentation

## Overview
This API provides two endpoints to handle kikoba member financial calculations, properly handling the fact that **users can belong to multiple vikobas** and need to see their totals for each specific kikoba.

---

## 🔑 Key Concepts

### Understanding the Kikoba-Member Relationship
- A **user** can be a member of **multiple vikobas**
- Each **kikoba** has its own **financial calculations** based on its type
- Each **membership** tracks a user's participation in a specific kikoba
- Totals are calculated **per kikoba**, not globally

**Example:**
```
User: John Doe (+255712345678)
├── Member of "Wanumeishuu" (KB000001) - Interest Refund VIKOBA
│   └── Total: 115,000 TZS
└── Member of "Tumaini" (KB000002) - Standard VIKOBA
    └── Total: 250,000 TZS
```

---

## 📡 API Endpoints

### 1. Get My Total in a Specific Kikoba (User-Specific)
**Recommended for Mobile Apps**

```http
GET /api/kikoba/{kikoba_id}/my_total/
```

**Description:** Returns the financial total for the **currently logged-in user** in the specified kikoba.

**Authentication:** Required (JWT Token)

**Parameters:**
- `kikoba_id` (path parameter): The ID of the kikoba

**Authorization:**
- User must be an active member of the specified kikoba
- Returns 404 if user is not a member

**Example Request:**
```bash
curl -X GET http://192.168.1.101:8000/api/kikoba/1/my_total/ \
  -H "Authorization: Bearer {token}"
```

**Example Response:**
```json
{
    "kikoba": {
        "id": 1,
        "name": "Wanumeishuu",
        "kikoba_number": "KB000001",
        "group_type": "interest_refund",
        "group_type_display": "Interest Refund VIKOBA"
    },
    "membership": {
        "membership_id": 15,
        "role": "member",
        "joined_at": "2025-11-10T10:30:00Z"
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
    "kikoba_summary": {
        "total_members": 5,
        "total_interest_collected": 50000.00,
        "total_fines_collected": 5000.00,
        "calculation_method": "Interest refunded to borrowers + equal share of fines"
    },
    "message": "Your total payout in Wanumeishuu is 115,000.00 TZS (Profit: 15,000.00 TZS)"
}
```

---

### 2. Get All Member Totals (Admin/Treasurer View)

```http
GET /api/kikoba/{kikoba_id}/member_totals/
```

**Description:** Returns financial totals for **all members** in the specified kikoba.

**Authentication:** Required (JWT Token)

**Parameters:**
- `kikoba_id` (path parameter): The ID of the kikoba

**Use Case:** For kikoba administrators, treasurers, or secretaries to view all member payouts

**Example Request:**
```bash
curl -X GET http://192.168.1.101:8000/api/kikoba/1/member_totals/ \
  -H "Authorization: Bearer {token}"
```

**Example Response:**
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
            "user_id": 5,
            "name": "John Doe",
            "phone_number": "+255712345678",
            "contribution": 100000.00,
            "shares": 10.0,
            "interest_paid": 15000.00,
            "total_payout": 115000.00,
            "profit": 15000.00
        },
        {
            "user_id": 8,
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
        "total_members": 5,
        "total_contributions": 500000.00,
        "total_payouts": 555000.00,
        "total_profit_distributed": 55000.00
    }
}
```

---

## 🚀 Mobile App Integration Examples

### Scenario 1: User Belongs to Multiple Vikobas

```javascript
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList } from 'react-native';

const MyVikobaTotals = () => {
  const [vikobas, setVikobas] = useState([]);
  const [totals, setTotals] = useState({});
  
  useEffect(() => {
    fetchMyVikobas();
  }, []);
  
  // Step 1: Get all vikobas the user is a member of
  const fetchMyVikobas = async () => {
    const token = await getAuthToken();
    const response = await fetch(
      'http://192.168.1.101:8000/api/users/me/my_vikoba/',
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    const data = await response.json();
    setVikobas(data);
    
    // Step 2: Fetch totals for each vikoba
    data.forEach(vikoba => {
      fetchMyTotalForKikoba(vikoba.kikoba.id);
    });
  };
  
  // Step 3: Get user's total for a specific kikoba
  const fetchMyTotalForKikoba = async (kikobaId) => {
    const token = await getAuthToken();
    const response = await fetch(
      `http://192.168.1.101:8000/api/kikoba/${kikobaId}/my_total/`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    const data = await response.json();
    
    setTotals(prev => ({
      ...prev,
      [kikobaId]: data
    }));
  };
  
  return (
    <View>
      <Text style={{fontSize: 20, fontWeight: 'bold'}}>My Vikoba Totals</Text>
      <FlatList
        data={vikobas}
        keyExtractor={(item) => item.kikoba.id.toString()}
        renderItem={({item}) => {
          const total = totals[item.kikoba.id];
          return (
            <View style={{padding: 15, borderWidth: 1, margin: 5}}>
              <Text style={{fontWeight: 'bold'}}>{item.kikoba.name}</Text>
              <Text>Kikoba: {item.kikoba.kikoba_number}</Text>
              <Text>Role: {item.role}</Text>
              {total && (
                <>
                  <Text>Contribution: {total.financial_data.contribution.toLocaleString()} TZS</Text>
                  <Text style={{color: 'green', fontWeight: 'bold'}}>
                    Total Payout: {total.financial_data.total_payout.toLocaleString()} TZS
                  </Text>
                  <Text style={{color: 'blue'}}>
                    Profit: {total.financial_data.profit.toLocaleString()} TZS
                  </Text>
                </>
              )}
            </View>
          );
        }}
      />
    </View>
  );
};
```

### Scenario 2: Single Kikoba View

```javascript
const SingleKikobaTotal = ({ kikobaId }) => {
  const [totalData, setTotalData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchMyTotal();
  }, [kikobaId]);
  
  const fetchMyTotal = async () => {
    try {
      setLoading(true);
      const token = await getAuthToken();
      const response = await fetch(
        `http://192.168.1.101:8000/api/kikoba/${kikobaId}/my_total/`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );
      
      if (response.status === 404) {
        // User is not a member of this kikoba
        alert('You are not a member of this kikoba');
        return;
      }
      
      const data = await response.json();
      setTotalData(data);
    } catch (error) {
      console.error('Error fetching total:', error);
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) return <Text>Loading...</Text>;
  if (!totalData) return <Text>No data</Text>;
  
  return (
    <View style={{padding: 20}}>
      <Text style={{fontSize: 24, fontWeight: 'bold'}}>
        {totalData.kikoba.name}
      </Text>
      <Text>{totalData.kikoba.group_type_display}</Text>
      
      <View style={{marginTop: 20, padding: 15, backgroundColor: '#f0f0f0'}}>
        <Text style={{fontSize: 18}}>Your Financial Summary</Text>
        <Text>Contribution: {totalData.financial_data.contribution.toLocaleString()} TZS</Text>
        <Text>Shares: {totalData.financial_data.shares}</Text>
        <Text>Interest Paid: {totalData.financial_data.interest_paid_on_loans.toLocaleString()} TZS</Text>
        
        <View style={{marginTop: 10, borderTopWidth: 1, paddingTop: 10}}>
          <Text style={{fontSize: 20, fontWeight: 'bold', color: 'green'}}>
            Total Payout: {totalData.financial_data.total_payout.toLocaleString()} TZS
          </Text>
          <Text style={{fontSize: 16, color: 'blue'}}>
            Profit: {totalData.financial_data.profit.toLocaleString()} TZS
          </Text>
        </View>
      </View>
      
      <Text style={{marginTop: 10, fontStyle: 'italic'}}>
        {totalData.message}
      </Text>
    </View>
  );
};
```

---

## 🔐 Authentication Flow

### Complete Flow from Login to Viewing Totals

```javascript
// 1. Login
const login = async (phoneNumber, pin) => {
  const response = await fetch('http://192.168.1.101:8000/api/token/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      phone_number: phoneNumber,
      password: pin,
    }),
  });
  const data = await response.json();
  
  // Store token
  await AsyncStorage.setItem('auth_token', data.access);
  await AsyncStorage.setItem('refresh_token', data.refresh);
  
  return data.access;
};

// 2. Get user's vikobas
const getMyVikobas = async (token) => {
  const response = await fetch(
    'http://192.168.1.101:8000/api/users/me/my_vikoba/',
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );
  return await response.json();
};

// 3. Get total for specific kikoba
const getMyTotalInKikoba = async (token, kikobaId) => {
  const response = await fetch(
    `http://192.168.1.101:8000/api/kikoba/${kikobaId}/my_total/`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );
  return await response.json();
};

// Usage
const token = await login('+255712345678', '1234');
const vikobas = await getMyVikobas(token);
const myTotal = await getMyTotalInKikoba(token, vikobas[0].kikoba.id);
```

---

## 🎯 Use Case Examples

### Use Case 1: User Dashboard - Show All My Vikobas and Totals
```
User logs in
  ↓
Fetch all vikobas: GET /api/users/me/my_vikoba/
  ↓
For each vikoba, fetch total: GET /api/kikoba/{id}/my_total/
  ↓
Display list with totals
```

### Use Case 2: Kikoba Details Page - My Total in This Kikoba
```
User selects a specific kikoba
  ↓
Fetch my total: GET /api/kikoba/{id}/my_total/
  ↓
Display contribution, payout, profit
```

### Use Case 3: Admin View - All Member Totals
```
Admin/Treasurer role
  ↓
Fetch all totals: GET /api/kikoba/{id}/member_totals/
  ↓
Display table of all members with their payouts
```

---

## 🛡️ Security & Data Isolation

### How the API Ensures Proper Isolation

1. **JWT Authentication:** Every request must include a valid JWT token
2. **User-Kikoba Verification:** The `/my_total/` endpoint checks that the logged-in user is a member
3. **Membership Filtering:** Only active memberships are considered
4. **Kikoba-Specific Calculations:** Each kikoba's calculations are isolated

### Error Handling

**User Not a Member:**
```json
{
    "detail": "You are not a member of this kikoba"
}
```
**Status Code:** 404

**No Active Members:**
```json
{
    "detail": "No active members in this kikoba"
}
```
**Status Code:** 404

**Authentication Failed:**
```json
{
    "detail": "Authentication credentials were not provided."
}
```
**Status Code:** 401

---

## 📊 Response Field Definitions

### `/my_total/` Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `kikoba.id` | integer | Kikoba database ID |
| `kikoba.name` | string | Kikoba name |
| `kikoba.kikoba_number` | string | Unique kikoba number (e.g., KB000001) |
| `kikoba.group_type` | string | Type code (standard, fixed_share, interest_refund, rosca) |
| `kikoba.group_type_display` | string | Human-readable type |
| `membership.membership_id` | integer | User's membership ID in this kikoba |
| `membership.role` | string | User's role (member, chairperson, treasurer, etc.) |
| `membership.joined_at` | datetime | When user joined this kikoba |
| `user.id` | integer | User ID |
| `user.name` | string | User's full name |
| `user.phone_number` | string | User's phone number |
| `financial_data.contribution` | decimal | Total amount contributed (TZS) |
| `financial_data.shares` | decimal | Number of shares (for standard VIKOBA) |
| `financial_data.interest_paid_on_loans` | decimal | Interest paid on loans (TZS) |
| `financial_data.total_payout` | decimal | Total amount to receive (TZS) |
| `financial_data.profit` | decimal | Profit earned (payout - contribution) |
| `kikoba_summary.total_members` | integer | Total members in kikoba |
| `kikoba_summary.total_interest_collected` | decimal | Total interest from all loans |
| `kikoba_summary.total_fines_collected` | decimal | Total fines collected |
| `kikoba_summary.calculation_method` | string | How payouts are calculated |
| `message` | string | Summary message |

---

## 🔄 Workflow Diagram

```
User: +255712345678 (John Doe)
│
├─ Member of Kikoba 1 (Wanumeishuu)
│  │
│  └─ GET /api/kikoba/1/my_total/
│     Returns: John's total in Wanumeishuu only
│     {
│       user: {id: 5, name: "John Doe"},
│       kikoba: {id: 1, name: "Wanumeishuu"},
│       financial_data: {
│         total_payout: 115000.00,
│         profit: 15000.00
│       }
│     }
│
└─ Member of Kikoba 2 (Tumaini)
   │
   └─ GET /api/kikoba/2/my_total/
      Returns: John's total in Tumaini only
      {
        user: {id: 5, name: "John Doe"},
        kikoba: {id: 2, name: "Tumaini"},
        financial_data: {
          total_payout: 250000.00,
          profit: 50000.00
        }
      }
```

---

## ✅ Summary

**Two Endpoints, Clear Purposes:**

1. **`/api/kikoba/{id}/my_total/`** - For regular members to see their own total
   - ✅ User-specific
   - ✅ Filtered by kikoba
   - ✅ Returns only authenticated user's data
   - ✅ Handles multiple memberships correctly

2. **`/api/kikoba/{id}/member_totals/`** - For admins to see all member totals
   - ✅ Shows all members
   - ✅ Useful for treasurers/admins
   - ✅ Complete financial overview

Both endpoints properly handle the **kikoba-member relationship** and ensure users see the correct data for each specific vikoba they belong to.
