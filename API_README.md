# MangiVikoba REST API - Quick Start Guide

## 📋 Overview

The MangiVikoba REST API provides comprehensive access to the Vikoba management system for mobile applications. This API supports user management, kikoba operations, savings tracking, loan management, and notifications.

## 🚀 Quick Start

### Base URL
```
Development: http://192.168.1.197:8000/api/v1/
Production: https://your-domain.com/api/v1/
```

### Authentication
The API uses JWT (JSON Web Token) authentication. 

1. **Register or Login** to get access tokens
2. **Include the access token** in all subsequent requests:
   ```
   Authorization: Bearer {your_access_token}
   ```

## 📚 Documentation Files

1. **API_DOCUMENTATION.md** - Complete API reference with all endpoints
2. **MangiVikoba_API.postman_collection.json** - Postman collection for testing
3. **test_api.py** - Python script to test API endpoints

## 🔑 Authentication Flow

### 1. Register a New User
```bash
POST /api/v1/users/
Content-Type: application/json

{
  "phone_number": "0712345678",
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "password_confirm": "SecurePassword123!",
  "role": "member"
}
```

### 2. Login (Get Tokens)
```bash
POST /api/v1/auth/token/
Content-Type: application/json

{
  "phone_number": "0712345678",
  "password": "SecurePassword123!"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 3. Use Access Token
```bash
GET /api/v1/users/me/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### 4. Refresh Token (When Access Token Expires)
```bash
POST /api/v1/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## 🎯 Key Features

### User Management
- Register new users
- Login/Authentication
- Profile management
- View user's vikoba

### Vikoba Operations
- Create and manage vikoba
- Join vikoba
- View members
- Check balances

### Savings & Contributions
- Record savings
- Confirm transactions
- Track member balances
- View saving history

### Loan Management
- Browse loan products
- Apply for loans
- Track loan applications
- Record repayments
- Verify repayments

### Notifications
- Receive notifications
- Mark as read
- View notification history

## 🧪 Testing the API

### Option 1: Using the Test Script
```bash
python test_api.py
```

### Option 2: Using Postman
1. Import `MangiVikoba_API.postman_collection.json` into Postman
2. Run the "Login (Get Token)" request
3. The collection will automatically save the access token
4. Test other endpoints

### Option 3: Using cURL
```bash
# Login
curl -X POST http://192.168.1.197:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"0712345678","password":"your_password"}'

# Get Profile
curl -X GET http://192.168.1.197:8000/api/v1/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 📱 Mobile App Integration

### Android (Kotlin/Java)
```kotlin
// Example using Retrofit
interface ApiService {
    @POST("auth/token/")
    suspend fun login(@Body credentials: LoginRequest): TokenResponse
    
    @GET("users/me/")
    suspend fun getCurrentUser(@Header("Authorization") token: String): User
    
    @GET("vikoba/")
    suspend fun getVikoba(@Header("Authorization") token: String): List<Kikoba>
}
```

### iOS (Swift)
```swift
// Example using URLSession
func login(phoneNumber: String, password: String) {
    let url = URL(string: "\(baseURL)/auth/token/")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    
    let body = ["phone_number": phoneNumber, "password": password]
    request.httpBody = try? JSONEncoder().encode(body)
    
    URLSession.shared.dataTask(with: request) { data, response, error in
        // Handle response
    }.resume()
}
```

### React Native
```javascript
// Example using fetch
const login = async (phoneNumber, password) => {
  const response = await fetch(`${BASE_URL}/auth/token/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      phone_number: phoneNumber,
      password: password,
    }),
  });
  
  const data = await response.json();
  return data;
};
```

## 🔒 Security Best Practices

1. **Never hardcode credentials** in your mobile app
2. **Store tokens securely** using:
   - iOS: Keychain
   - Android: EncryptedSharedPreferences
3. **Implement token refresh** logic
4. **Clear tokens on logout**
5. **Use HTTPS** in production
6. **Validate all input** before sending to API

## 📊 API Response Format

### Success Response
```json
{
  "id": 1,
  "field1": "value1",
  "field2": "value2"
}
```

### List Response (Paginated)
```json
{
  "count": 100,
  "next": "http://api.com/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

### Error Response
```json
{
  "detail": "Error message",
  "field_name": ["Field-specific error"]
}
```

## 🎨 Common Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid input data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## 🔍 Filtering & Searching

### Filter by Field
```
GET /api/v1/vikoba/?is_active=true
GET /api/v1/savings/?status=confirmed
```

### Search
```
GET /api/v1/users/?search=john
GET /api/v1/vikoba/?search=savings
```

### Ordering
```
GET /api/v1/savings/?ordering=-transaction_date
GET /api/v1/loans/?ordering=disbursement_date
```

### Pagination
```
GET /api/v1/vikoba/?page=2&page_size=50
```

## 📞 Support

For API support and questions:
- Email: support@mangivivoba.com
- Documentation: See `API_DOCUMENTATION.md`
- Test Server: http://192.168.1.197:8000/api/v1/

## 🔄 API Versioning

Current Version: **v1**

All endpoints are prefixed with `/api/v1/` to support future versioning.

## ⚡ Rate Limiting

Currently, no rate limiting is implemented in development. Production may have rate limits to ensure fair usage.

## 🌐 CORS

CORS is enabled for all origins in development. Production will have specific allowed origins.

## 📝 Changelog

### Version 1.0.0 (2025-10-16)
- Initial API release
- User authentication with JWT
- Vikoba management
- Savings tracking
- Loan management
- Notifications system
- Complete CRUD operations for all models

---

**Happy Coding! 🚀**
