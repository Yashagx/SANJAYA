# SANJAYA Login System

## Overview

The SANJAYA application includes a complete authentication system with:
- User registration
- Login with email/password
- JWT token-based authentication
- Admin user management
- Secure password hashing with bcrypt

---

## Getting Started

### 1. Register a New User

**Endpoint:** `POST /auth/register`

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_email": "user@example.com",
  "is_admin": false
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character (!@#$%^&*)

**Email Requirements:**
- Valid email format
- Must not already exist in the database

---

### 2. Login to Your Account

**Via Web UI:**
1. Go to `http://localhost:8000/login`
2. Enter your email and password
3. Click "Login"
4. You'll receive a token that's stored in your browser

**Via API:**

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_email": "user@example.com",
  "is_admin": false
}
```

---

### 3. Access Protected Endpoints

Use your access token to call protected endpoints:

```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response:**
```json
{
  "email": "user@example.com",
  "is_admin": false,
  "created_at": "N/A"
}
```

---

## Protected Endpoints

Only authenticated users can access these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/me` | GET | Get current user info |
| `/logs` | GET | View application logs (admin only) |
| `/predict` | POST | Run risk assessment |
| `/history` | GET | View assessment history |

---

## JWT Token Information

**Token Type:** Bearer Token  
**Algorithm:** HS256  
**Expiration:** 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)  
**Payload:**
```json
{
  "sub": "user@example.com",
  "is_admin": false,
  "exp": 1234567890
}
```

---

## Usage Examples

### 1. Register and Login Flow

```bash
# Step 1: Register
RESPONSE=$(curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test@123456"}')

TOKEN=$(echo $RESPONSE | jq -r '.access_token')
echo "Token: $TOKEN"

# Step 2: Use token for requests
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Step 3: Access protected endpoints
curl -X POST http://localhost:8000/predict \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"origin":"Shanghai","destination":"Rotterdam"}'
```

### 2. Automated Token Refresh

Tokens expire after 30 minutes. You must log in again to get a new token:

```bash
# Old token expired? Get a new one
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test@123456"}'
```

---

## Security Features

✅ **Passwords are hashed** using bcrypt (never stored in plain text)  
✅ **JWT tokens are signed** using a secret key (HS256)  
✅ **Tokens expire** after 30 minutes for security  
✅ **Email format validation** prevents invalid entries  
✅ **Password strength validation** enforces secure passwords  
✅ **HTTP Bearer authentication** for API access  

---

## Admin User Setup

To create an admin user (first-time setup on EC2):

```bash
# Register the first user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"SecurePassword123!"}'

# Then manually set is_admin=1 in the database
ssh -i your-key.pem ec2-user@16.112.128.251 << EOF
sudo -u postgres psql sanjaya_db << DBSQL
UPDATE users SET is_admin = 1 WHERE email = 'admin@example.com';
DBSQL
EOF
```

Once admin is set up:

```bash
# Admin can view logs
TOKEN="your_admin_token_here"
curl -X GET "http://localhost:8000/logs?limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Troubleshooting

### "Invalid credentials" on login

- Verify email is correct (case-sensitive?)
- Check if password is correct
- Verify user exists: `sudo -u postgres psql sanjaya_db -c "SELECT email FROM users;"`

### "Weak password" on registration

Your password must have:
- ✓ At least 8 characters
- ✓ One uppercase letter (A-Z)
- ✓ One lowercase letter (a-z)
- ✓ One number (0-9)
- ✓ One special character (!@#$%^&*)

Good example: `SecurePass123!`

### "User already exists" on registration

That email is already registered. Either:
1. Use a different email address
2. Login with your existing account
3. Reset your password (if implemented)

### Token invalid/expired

Tokens expire after 30 minutes. Login again:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"YourPassword123!"}'
```

---

## API Reference

### Register

```
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

Response 200:
{
  "access_token": "string",
  "token_type": "bearer",
  "user_email": "user@example.com",
  "is_admin": false
}
```

### Login

```
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

Response 200:
{
  "access_token": "string",
  "token_type": "bearer",
  "user_email": "user@example.com",
  "is_admin": false
}
```

### Get Current User

```
GET /auth/me
Authorization: Bearer <token>

Response 200:
{
  "email": "user@example.com",
  "is_admin": false,
  "created_at": "N/A"
}
```

---

## Next Steps

1. **Register your first user** using the registration endpoint
2. **Login** and get your JWT token
3. **Use your token** to access protected endpoints like `/predict`
4. **View your risk assessments** in real-time

**Your SANJAYA system is now ready to use! 🚀**
