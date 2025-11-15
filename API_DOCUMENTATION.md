# MangiVikoba REST API Documentation

## Base URL
```
Development: http://192.168.1.197:8000/api/v1/
Production: https://your-domain.com/api/v1/
```

## Authentication

The API uses JWT (JSON Web Token) authentication. All endpoints (except registration and login) require authentication.

### Get Access Token (Login)
**Endpoint:** `POST /api/v1/auth/token/`

**Request Body:**
```json
{
  "phone_number": "0712345678",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Refresh Access Token
**Endpoint:** `POST /api/v1/auth/token/refresh/`

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Using the Token
Include the access token in all API requests:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## Endpoints Overview

### Users
- `GET /api/v1/users/` - List all users
- `POST /api/v1/users/` - Register new user (no auth required)
- `GET /api/v1/users/{id}/` - Get user details
- `PUT /api/v1/users/{id}/` - Update user
- `DELETE /api/v1/users/{id}/` - Delete user
- `GET /api/v1/users/me/` - Get current user profile
- `GET /api/v1/users/my_vikoba/` - Get current user's vikoba

### Vikoba (Groups)
- `GET /api/v1/vikoba/` - List all vikoba
- `POST /api/v1/vikoba/` - Create new kikoba
- `GET /api/v1/vikoba/{id}/` - Get kikoba details
- `PUT /api/v1/vikoba/{id}/` - Update kikoba
- `DELETE /api/v1/vikoba/{id}/` - Delete kikoba
- `GET /api/v1/vikoba/{id}/members/` - Get kikoba members
- `GET /api/v1/vikoba/{id}/balance/` - Get kikoba balance
- `POST /api/v1/vikoba/{id}/join/` - Join a kikoba

### Memberships
- `GET /api/v1/memberships/` - List memberships
- `POST /api/v1/memberships/` - Create membership
- `GET /api/v1/memberships/{id}/` - Get membership details
- `PUT /api/v1/memberships/{id}/` - Update membership
- `DELETE /api/v1/memberships/{id}/` - Delete membership

### Invitations
- `GET /api/v1/invitations/` - List invitations
- `POST /api/v1/invitations/` - Create invitation
- `GET /api/v1/invitations/{id}/` - Get invitation details
- `POST /api/v1/invitations/{id}/accept/` - Accept invitation
- `POST /api/v1/invitations/{id}/reject/` - Reject invitation

### Savings
- `GET /api/v1/savings/` - List savings
- `POST /api/v1/savings/` - Create saving record
- `GET /api/v1/savings/{id}/` - Get saving details
- `POST /api/v1/savings/{id}/confirm/` - Confirm saving
- `POST /api/v1/savings/{id}/reject/` - Reject saving

### Contributions
- `GET /api/v1/contributions/` - List contributions
- `POST /api/v1/contributions/` - Create contribution
- `GET /api/v1/contributions/{id}/` - Get contribution details

### Balances
- `GET /api/v1/member-balances/` - List member balances
- `GET /api/v1/member-balances/{id}/` - Get member balance details
- `GET /api/v1/kikoba-balances/` - List kikoba balances
- `GET /api/v1/kikoba-balances/{id}/` - Get kikoba balance details

### Loan Products
- `GET /api/v1/loan-products/` - List loan products
- `POST /api/v1/loan-products/` - Create loan product
- `GET /api/v1/loan-products/{id}/` - Get loan product details

### Loan Applications
- `GET /api/v1/loan-applications/` - List loan applications
- `POST /api/v1/loan-applications/` - Create loan application
- `GET /api/v1/loan-applications/{id}/` - Get application details
- `POST /api/v1/loan-applications/{id}/approve/` - Approve application
- `POST /api/v1/loan-applications/{id}/reject/` - Reject application

### Loans
- `GET /api/v1/loans/` - List loans
- `POST /api/v1/loans/` - Create loan
- `GET /api/v1/loans/{id}/` - Get loan details

### Repayments
- `GET /api/v1/repayments/` - List repayments
- `POST /api/v1/repayments/` - Create repayment
- `GET /api/v1/repayments/{id}/` - Get repayment details
- `POST /api/v1/repayments/{id}/verify/` - Verify repayment

### Notifications
- `GET /api/v1/notifications/` - List notifications
- `GET /api/v1/notifications/{id}/` - Get notification details
- `POST /api/v1/notifications/{id}/mark_read/` - Mark as read
- `POST /api/v1/notifications/mark_all_read/` - Mark all as read

---

## Detailed Endpoint Examples

### 1. User Registration
**Endpoint:** `POST /api/v1/users/`

**Request Body:**
```json
{
  "phone_number": "0712345678",
  "name": "John Doe",
  "email": "john@example.com",
  "password": "secure_password",
  "password_confirm": "secure_password",
  "role": "member"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "phone_number": "0712345678",
  "name": "John Doe",
  "email": "john@example.com",
  "role": "member",
  "nida_number": null,
  "phone_number_verified": false,
  "profile_photo": null,
  "verification_method": null,
  "verification_status": "pending",
  "date_joined": "2025-10-16T08:00:00Z",
  "is_active": true
}
```

### 2. Get Current User Profile
**Endpoint:** `GET /api/v1/users/me/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "phone_number": "0712345678",
  "name": "John Doe",
  "email": "john@example.com",
  "role": "member",
  "nida_number": null,
  "phone_number_verified": false,
  "profile_photo": null,
  "verification_method": null,
  "verification_status": "pending",
  "date_joined": "2025-10-16T08:00:00Z",
  "is_active": true
}
```

### 3. Create Kikoba
**Endpoint:** `POST /api/v1/vikoba/`

**Request Body:**
```json
{
  "name": "My Kikoba",
  "description": "A savings group for our community",
  "contribution_frequency": "monthly",
  "interest_rate": "5.00",
  "loan_limit_factor": "3.00",
  "loan_term_days": 90,
  "late_payment_penalty": "1.00",
  "is_center_kikoba": true,
  "location": "Dar es Salaam",
  "estimated_members": "11-20"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "name": "My Kikoba",
  "description": "A savings group for our community",
  "created_by": 1,
  "created_by_name": "John Doe",
  "created_at": "2025-10-16T08:00:00Z",
  "contribution_frequency": "monthly",
  "interest_rate": "5.00",
  "loan_limit_factor": "3.00",
  "loan_term_days": 90,
  "late_payment_penalty": "1.00",
  "is_active": true,
  "is_center_kikoba": true,
  "location": "Dar es Salaam",
  "estimated_members": "11-20",
  "kikoba_number": "KB000001",
  "member_count": 1,
  "contribution_config": null
}
```

### 4. Get User's Vikoba
**Endpoint:** `GET /api/v1/users/my_vikoba/`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "My Kikoba",
    "description": "A savings group",
    "created_by": 1,
    "created_by_name": "John Doe",
    "created_at": "2025-10-16T08:00:00Z",
    "contribution_frequency": "monthly",
    "interest_rate": "5.00",
    "member_count": 5,
    "kikoba_number": "KB000001"
  }
]
```

### 5. Create Saving
**Endpoint:** `POST /api/v1/savings/`

**Request Body:**
```json
{
  "group": 1,
  "member": 1,
  "amount": "50000.00",
  "transaction_reference": "MPESA123456",
  "notes": "Monthly savings contribution"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "group": 1,
  "group_name": "My Kikoba",
  "member": 1,
  "member_name": "John Doe",
  "amount": "50000.00",
  "transaction_date": "2025-10-16T08:00:00Z",
  "status": "pending",
  "confirmed_by": null,
  "confirmed_by_name": null,
  "confirmation_date": null,
  "transaction_reference": "MPESA123456",
  "notes": "Monthly savings contribution"
}
```

### 6. Apply for Loan
**Endpoint:** `POST /api/v1/loan-applications/`

**Request Body:**
```json
{
  "kikoba": 1,
  "loan_product": 1,
  "requested_amount": "100000.00",
  "purpose": "Business expansion"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "member": 1,
  "member_name": "John Doe",
  "kikoba": 1,
  "kikoba_name": "My Kikoba",
  "loan_product": 1,
  "loan_product_name": "Emergency Loan",
  "requested_amount": "100000.00",
  "purpose": "Business expansion",
  "application_date": "2025-10-16T08:00:00Z",
  "status": "pending",
  "decision_date": null,
  "decision_by": null,
  "decision_by_name": null,
  "remarks": null
}
```

### 7. List Notifications
**Endpoint:** `GET /api/v1/notifications/`

**Query Parameters:**
- `is_read` - Filter by read status (true/false)

**Response:** `200 OK`
```json
{
  "count": 10,
  "next": "http://192.168.1.197:8000/api/v1/notifications/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": 1,
      "message": "Your loan application has been approved",
      "is_read": false,
      "created_at": "2025-10-16T08:00:00Z"
    }
  ]
}
```

---

## Filtering and Searching

Most list endpoints support filtering, searching, and ordering:

### Filtering
Add query parameters to filter results:
```
GET /api/v1/vikoba/?is_active=true
GET /api/v1/savings/?status=confirmed
GET /api/v1/loan-applications/?status=pending
```

### Searching
Search across specified fields:
```
GET /api/v1/users/?search=john
GET /api/v1/vikoba/?search=savings
```

### Ordering
Order results by specified fields:
```
GET /api/v1/savings/?ordering=-transaction_date
GET /api/v1/loan-applications/?ordering=application_date
```

Use `-` prefix for descending order.

---

## Pagination

All list endpoints are paginated with 20 items per page by default.

**Response Structure:**
```json
{
  "count": 100,
  "next": "http://192.168.1.197:8000/api/v1/vikoba/?page=2",
  "previous": null,
  "results": [...]
}
```

**Query Parameters:**
- `page` - Page number (default: 1)
- `page_size` - Items per page (max: 100)

Example:
```
GET /api/v1/vikoba/?page=2&page_size=50
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid input data",
  "field_name": ["Error message"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Testing the API

### Using cURL

**Login:**
```bash
curl -X POST http://192.168.1.197:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"0712345678","password":"your_password"}'
```

**Get Profile:**
```bash
curl -X GET http://192.168.1.197:8000/api/v1/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Using Postman

1. Import the base URL: `http://192.168.1.197:8000/api/v1/`
2. Set up authentication:
   - Type: Bearer Token
   - Token: Your access token
3. Start making requests to the endpoints

### Using Python (requests library)

```python
import requests

# Login
response = requests.post(
    'http://192.168.1.197:8000/api/v1/auth/token/',
    json={
        'phone_number': '0712345678',
        'password': 'your_password'
    }
)
access_token = response.json()['access']

# Get profile
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get(
    'http://192.168.1.197:8000/api/v1/users/me/',
    headers=headers
)
user_data = response.json()
```

---

## Best Practices

1. **Token Management**
   - Store tokens securely on the mobile device
   - Implement token refresh logic before expiration
   - Clear tokens on logout

2. **Error Handling**
   - Always check response status codes
   - Handle network errors gracefully
   - Display user-friendly error messages

3. **Pagination**
   - Implement infinite scrolling or pagination in your mobile app
   - Load data progressively

4. **Caching**
   - Cache frequently accessed data locally
   - Implement offline mode where possible

5. **Performance**
   - Use filtering and field selection to reduce payload size
   - Batch requests when possible

---

## Support

For API issues or questions, contact the development team.

**Development Server:** http://192.168.1.197:8000/api/v1/
**API Browser:** http://192.168.1.197:8000/api/v1/ (when logged in via browser)
