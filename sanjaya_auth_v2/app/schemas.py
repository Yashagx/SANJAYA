from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: str
    password: str = Field(min_length=8)
    role: str = Field(default="user")
    mfa_enabled: bool = True


class LoginRequest(BaseModel):
    username: str
    password: str


class VerifyMFARequest(BaseModel):
    challenge_id: str
    otp: str = Field(min_length=6, max_length=6)


class RefreshRequest(BaseModel):
    refresh_token: str


class GoogleLoginRequest(BaseModel):
    id_token: str


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    redirect_url: str


class MFAPendingResponse(BaseModel):
    mfa_required: bool = True
    challenge_id: str
    expires_in_seconds: int
    delivery_channel: str
    debug_otp: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    mfa_enabled: bool
    is_active: bool
    created_at: datetime


class MessageResponse(BaseModel):
    message: str


# ── Admin schemas ─────────────────────────────────────────────────────────────

class AdminUpdateRoleRequest(BaseModel):
    role: str = Field(pattern="^(user|manager|admin)$")


class AdminToggleActiveRequest(BaseModel):
    is_active: bool


class AdminUserResponse(BaseModel):
    id: str
    username: str
    role: str
    mfa_enabled: bool
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    email_masked: str


class AuditLogResponse(BaseModel):
    id: str
    timestamp: datetime
    user_id: Optional[str] = None
    username: Optional[str] = None
    action: str
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    status: str
