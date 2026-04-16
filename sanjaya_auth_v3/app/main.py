import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import desc
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db, SessionLocal
from .deps import get_current_user, require_admin, require_manager_or_above
from .emailer import send_mfa_code_email
from .models import AuditLog, MFAChallenge, RefreshToken, User
from .schemas import (
    AdminToggleActiveRequest,
    AdminUpdateRoleRequest,
    AdminUserResponse,
    AuditLogResponse,
    AuthTokens,
    LoginRequest,
    MFAPendingResponse,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    UserResponse,
    VerifyMFARequest,
)
from .security import (
    create_access_token,
    decrypt_pii,
    encrypt_pii,
    generate_otp_code,
    generate_refresh_token,
    hash_email,
    hash_otp,
    hash_password,
    hash_refresh_token,
    mask_email,
    verify_password,
)

logger = logging.getLogger("auth")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.app_name, version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent.parent / "static"


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    if not settings.pii_encryption_key:
        raise RuntimeError("PII_ENCRYPTION_KEY is required — check your .env file")
    
    db = SessionLocal()
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        user = User(
            username="admin",
            email_encrypted=encrypt_pii("admin@local.host"),
            email_hash=hash_email("admin@local.host"),
            password_hash=hash_password("admin"),
            role="admin",
            mfa_enabled=False,
            is_active=True
        )
        db.add(user)
        db.commit()
    db.close()


def _now_utc() -> datetime:
    return datetime.utcnow()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _audit(db: Session, action: str, request: Request = None,
           user_id: str = None, username: str = None,
           detail: str = None, status_val: str = "success"):
    ip_addr = _client_ip(request) if request else "System"
    ip_with_port = f"{ip_addr} (Port: 8001)"
    log = AuditLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        username=username,
        action=action,
        detail=detail,
        ip_address=ip_with_port,
        status=status_val,
    )
    db.add(log)
    db.commit()


def _issue_tokens(db: Session, user: User) -> AuthTokens:
    access_token, expires_in = create_access_token(
        subject=user.id, username=user.username, role=user.role
    )
    refresh_raw, refresh_hash, refresh_exp = generate_refresh_token()

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=refresh_exp,
        )
    )
    db.commit()

    if user.role == "admin":
        redirect_url = "/admin.html"
    else:
        redirect_url = settings.post_login_redirect_url

    return AuthTokens(
        access_token=access_token,
        refresh_token=refresh_raw,
        expires_in=expires_in,
        redirect_url=redirect_url,
    )


def _create_mfa_challenge(db: Session, user: User) -> MFAPendingResponse:
    challenge_id = str(uuid.uuid4())
    otp = generate_otp_code()

    challenge = MFAChallenge(
        id=challenge_id,
        user_id=user.id,
        code_hash=hash_otp(challenge_id, otp),
        expires_at=_now_utc().replace(microsecond=0) + timedelta(seconds=settings.mfa_code_ttl_seconds),
        purpose="login",
    )
    db.add(challenge)
    db.commit()

    email = decrypt_pii(user.email_encrypted)
    sent = send_mfa_code_email(email, otp)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to deliver MFA code. Check SMTP settings in .env",
        )

    return MFAPendingResponse(
        challenge_id=challenge_id,
        expires_in_seconds=settings.mfa_code_ttl_seconds,
        delivery_channel="email",
        debug_otp=otp if settings.debug_otp_in_response else None,
    )


# ─────────────────────────────────────────────────────────────────────────────
# FRONTEND — Serve the SPA
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def serve_root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>SANJAYA Auth</h1><p>static/index.html not found</p>")


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/admin.html", response_class=HTMLResponse)
def serve_admin():
    file_path = STATIC_DIR / "admin.html"
    if file_path.exists():
        return HTMLResponse(content=file_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Admin File Missing</h1>", status_code=404)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "sanjaya-auth", "env": settings.environment}


@app.post("/auth/register", response_model=UserResponse)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    email_hash_value = hash_email(payload.email)

    existing = (
        db.query(User)
        .filter((User.username == payload.username) | (User.email_hash == email_hash_value))
        .first()
    )
    if existing:
        _audit(db, "register", request, username=payload.username,
               detail="Duplicate username or email", status_val="failure")
        raise HTTPException(status_code=409, detail="Username or email already exists")

    user = User(
        username=payload.username,
        email_encrypted=encrypt_pii(payload.email.strip().lower()),
        email_hash=email_hash_value,
        password_hash=hash_password(payload.password),
        role="user",  # All self-registrations are 'user'; admin promotes via panel
        mfa_enabled=payload.mfa_enabled,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    _audit(db, "register", request, user_id=user.id, username=user.username,
           detail="New user registered (role=user)")

    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        mfa_enabled=user.mfa_enabled,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@app.post("/auth/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not user.is_active:
        _audit(db, "login", request, username=payload.username,
               detail="Invalid credentials or inactive", status_val="failure")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.password_hash or not verify_password(payload.password, user.password_hash):
        _audit(db, "login", request, user_id=user.id, username=user.username,
               detail="Wrong password", status_val="failure")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    _audit(db, "login", request, user_id=user.id, username=user.username,
           detail=f"Login successful, MFA={user.mfa_enabled}")

    if user.mfa_enabled:
        return _create_mfa_challenge(db, user)

    user.last_login_at = _now_utc()
    db.commit()
    return _issue_tokens(db, user)


@app.post("/auth/verify-mfa", response_model=AuthTokens)
def verify_mfa(payload: VerifyMFARequest, request: Request, db: Session = Depends(get_db)):
    challenge = db.query(MFAChallenge).filter(MFAChallenge.id == payload.challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="MFA challenge not found")
    if challenge.consumed_at is not None:
        raise HTTPException(status_code=400, detail="MFA challenge already used")
    if challenge.expires_at < _now_utc():
        raise HTTPException(status_code=400, detail="MFA challenge expired")
    if challenge.attempts >= settings.mfa_max_attempts:
        raise HTTPException(status_code=429, detail="Too many failed OTP attempts")

    expected_hash = hash_otp(challenge.id, payload.otp)
    if expected_hash != challenge.code_hash:
        challenge.attempts += 1
        db.commit()
        _audit(db, "mfa_verify", request, user_id=challenge.user_id,
               detail=f"Wrong OTP attempt {challenge.attempts}", status_val="failure")
        raise HTTPException(status_code=401, detail="Invalid OTP")

    challenge.consumed_at = _now_utc()
    user = db.query(User).filter(User.id == challenge.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid user")

    user.last_login_at = _now_utc()
    db.commit()

    _audit(db, "mfa_verify", request, user_id=user.id, username=user.username,
           detail="MFA verified successfully")

    return _issue_tokens(db, user)


@app.post("/auth/refresh", response_model=AuthTokens)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    token_row = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash, RefreshToken.revoked_at.is_(None))
        .first()
    )
    if not token_row or token_row.expires_at < _now_utc():
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.id == token_row.user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    token_row.revoked_at = _now_utc()
    db.commit()
    return _issue_tokens(db, user)


@app.post("/auth/logout", response_model=MessageResponse)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    token_row = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash, RefreshToken.revoked_at.is_(None))
        .first()
    )
    if token_row:
        token_row.revoked_at = _now_utc()
        db.commit()
    return MessageResponse(message="Logged out successfully")


@app.get("/auth/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "mfa_enabled": current_user.mfa_enabled,
        "is_active": current_user.is_active,
        "email_masked": mask_email(decrypt_pii(current_user.email_encrypted)),
        "redirect_url": settings.post_login_redirect_url,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN ENDPOINTS — Full RBAC management + audit logs
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/admin/users", response_model=list[AdminUserResponse])
def admin_list_users(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    users = db.query(User).order_by(desc(User.created_at)).all()
    result = []
    for u in users:
        try:
            email_masked = mask_email(decrypt_pii(u.email_encrypted))
        except Exception:
            email_masked = "***@***"
        result.append(AdminUserResponse(
            id=u.id,
            username=u.username,
            role=u.role,
            mfa_enabled=u.mfa_enabled,
            is_active=u.is_active,
            created_at=u.created_at,
            last_login_at=u.last_login_at,
            email_masked=email_masked,
        ))
    return result


@app.post("/admin/users", response_model=AdminUserResponse)
def admin_create_user(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    email_hash_value = hash_email(payload.email)
    existing = db.query(User).filter((User.username == payload.username) | (User.email_hash == email_hash_value)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username or email already exists")

    user = User(
        username=payload.username,
        email_encrypted=encrypt_pii(payload.email.strip().lower()),
        email_hash=email_hash_value,
        password_hash=hash_password(payload.password),
        role=payload.role,
        mfa_enabled=payload.mfa_enabled,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    _audit(db, "admin_create_user", request, user_id=user.id, username=user.username,
           detail=f"Created by {admin.username} (role={user.role})")
           
    email_masked = "***@***"
    try:
        email_masked = mask_email(payload.email)
    except:
        pass

    return AdminUserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        mfa_enabled=user.mfa_enabled,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        email_masked=email_masked,
    )


@app.put("/admin/users/{user_id}/role", response_model=MessageResponse)
def admin_update_role(
    user_id: str,
    payload: AdminUpdateRoleRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    old_role = user.role
    user.role = payload.role
    db.commit()
    _audit(db, "admin_change_role", request, user_id=user.id, username=user.username,
           detail=f"Role changed: {old_role} → {payload.role} by {admin.username}")
    return MessageResponse(message=f"Role updated to {payload.role}")


@app.put("/admin/users/{user_id}/active", response_model=MessageResponse)
def admin_toggle_active(
    user_id: str,
    payload: AdminToggleActiveRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = payload.is_active
    db.commit()
    _audit(db, "admin_toggle_active", request, user_id=user.id, username=user.username,
           detail=f"Active set to {payload.is_active} by {admin.username}")
    return MessageResponse(message=f"User {'activated' if payload.is_active else 'deactivated'}")


@app.get("/admin/logs", response_model=list[AuditLogResponse])
def admin_get_logs(
    limit: int = 200,
    action: Optional[str] = None,
    username: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    q = db.query(AuditLog).order_by(desc(AuditLog.timestamp))
    if action:
        q = q.filter(AuditLog.action == action)
    if username:
        q = q.filter(AuditLog.username == username)
    if status_filter:
        q = q.filter(AuditLog.status == status_filter)
    logs = q.limit(limit).all()
    return [
        AuditLogResponse(
            id=log.id,
            timestamp=log.timestamp,
            user_id=log.user_id,
            username=log.username,
            action=log.action,
            detail=log.detail,
            ip_address=log.ip_address,
            status=log.status,
        )
        for log in logs
    ]


@app.get("/admin/stats")
def admin_stats(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active.is_(True)).count()
    admins = db.query(User).filter(User.role == "admin").count()
    managers = db.query(User).filter(User.role == "manager").count()
    total_logs = db.query(AuditLog).count()
    failed_logins = db.query(AuditLog).filter(
        AuditLog.action == "login", AuditLog.status == "failure"
    ).count()
    return {
        "total_users": total_users,
        "active_users": active_users,
        "admins": admins,
        "managers": managers,
        "total_logs": total_logs,
        "failed_logins": failed_logins,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MANAGER ENDPOINTS — Read-only user list
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/manager/users", response_model=list[AdminUserResponse])
def manager_list_users(db: Session = Depends(get_db), _mgr: User = Depends(require_manager_or_above)):
    users = db.query(User).order_by(desc(User.created_at)).all()
    result = []
    for u in users:
        try:
            email_masked = mask_email(decrypt_pii(u.email_encrypted))
        except Exception:
            email_masked = "***@***"
        result.append(AdminUserResponse(
            id=u.id,
            username=u.username,
            role=u.role,
            mfa_enabled=u.mfa_enabled,
            is_active=u.is_active,
            created_at=u.created_at,
            last_login_at=u.last_login_at,
            email_masked=email_masked,
        ))
    return result


@app.get("/manager/stats")
def manager_stats(db: Session = Depends(get_db), _mgr: User = Depends(require_manager_or_above)):
    return {
        "total_users": db.query(User).count(),
        "active_users": db.query(User).filter(User.is_active.is_(True)).count(),
    }
