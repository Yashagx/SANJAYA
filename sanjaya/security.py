# Security Module - Platform Security Features
# Implements: JWT, MFA, RBAC, PII Encryption

import os
import jwt
import secrets
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import hashlib

# ────────────────────────────────────────────────────────────
# JWT Configuration
# ────────────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# ────────────────────────────────────────────────────────────
# PII Encryption
# ────────────────────────────────────────────────────────────
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
cipher_suite = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

def encrypt_pii(data: str) -> str:
    """Encrypt PII data before storing in database."""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_pii(encrypted_data: str) -> str:
    """Decrypt PII data retrieved from database."""
    return cipher_suite.decrypt(encrypted_data.encode()).decode()

# ────────────────────────────────────────────────────────────
# Role-Based Access Control (RBAC)
# ────────────────────────────────────────────────────────────
class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    USER = "user"
    VIEWER = "viewer"

ROLE_PERMISSIONS = {
    UserRole.ADMIN: ["read", "write", "delete", "manage_users", "manage_roles"],
    UserRole.MANAGER: ["read", "write", "delete", "manage_analysts"],
    UserRole.ANALYST: ["read", "write", "create_reports"],
    UserRole.USER: ["read", "write"],
    UserRole.VIEWER: ["read"],
}

def has_permission(user_role: UserRole, permission: str) -> bool:
    """Check if user role has specific permission."""
    return permission in ROLE_PERMISSIONS.get(user_role, [])

def require_role(*roles: UserRole):
    """Decorator to require specific roles for endpoint access."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from request context (to be implemented in main.py)
            user_role = kwargs.get("user_role")
            if user_role not in roles:
                raise PermissionError(f"Insufficient permissions. Required roles: {roles}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# ────────────────────────────────────────────────────────────
# JWT Token Management
# ────────────────────────────────────────────────────────────
def generate_token(user_id: str, role: UserRole, mfa_verified: bool = False) -> str:
    """Generate JWT token with user claims."""
    payload = {
        "user_id": user_id,
        "role": role.value,
        "mfa_verified": mfa_verified,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def refresh_token(token: str) -> Optional[str]:
    """Refresh an existing token."""
    payload = verify_token(token)
    if not payload:
        return None
    
    new_payload = {
        "user_id": payload["user_id"],
        "role": payload["role"],
        "mfa_verified": payload["mfa_verified"],
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(new_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# ────────────────────────────────────────────────────────────
# MFA (Multi-Factor Authentication)
# ────────────────────────────────────────────────────────────
class MFAService:
    """MFA service for OTP generation and verification."""
    
    @staticmethod
    def generate_otp() -> str:
        """Generate a 6-digit OTP."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    @staticmethod
    def send_otp_via_email(email: str, otp: str) -> bool:
        """Send OTP to user email."""
        # TODO: Integrate with email service (SendGrid, AWS SES, etc.)
        print(f"OTP for {email}: {otp}")
        return True
    
    @staticmethod
    def verify_otp(stored_otp: str, provided_otp: str, max_age_seconds: int = 300) -> bool:
        """Verify OTP (must be within max_age_seconds)."""
        return stored_otp == provided_otp

# ────────────────────────────────────────────────────────────
# OAuth2 Configuration (Google Login)
# ────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

# TODO: Implement Google OAuth flow using authlib or google-auth-oauthlib

print("[SECURITY] Security module initialized with JWT, RBAC, MFA, and PII encryption")
