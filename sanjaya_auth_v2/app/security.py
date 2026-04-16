import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _now_utc() -> datetime:
    return datetime.utcnow()


def _fernet() -> Fernet:
    key = settings.pii_encryption_key
    if not key:
        raise RuntimeError("PII_ENCRYPTION_KEY is required")
    return Fernet(key.encode("utf-8"))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def hash_email(email: str) -> str:
    normalized = email.strip().lower().encode("utf-8")
    salt = settings.pii_hash_salt.encode("utf-8")
    return hmac.new(salt, normalized, hashlib.sha256).hexdigest()


def encrypt_pii(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_pii(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt PII") from exc


def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[:2] + "*" * (len(local) - 2)
    return f"{masked_local}@{domain}"


def create_access_token(subject: str, username: str, role: str) -> tuple[str, int]:
    expires_delta = timedelta(minutes=settings.access_token_minutes)
    expires_at = _now_utc() + expires_delta
    payload = {
        "sub": subject,
        "username": username,
        "role": role,
        "type": "access",
        "exp": int(expires_at.timestamp()),
        "iat": int(_now_utc().timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(expires_delta.total_seconds())


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != "access":
        raise JWTError("Invalid token type")
    return payload


def generate_refresh_token() -> tuple[str, str, datetime]:
    raw = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    expires_at = _now_utc() + timedelta(days=settings.refresh_token_days)
    return raw, token_hash, expires_at


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_otp_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def hash_otp(challenge_id: str, otp: str) -> str:
    material = f"{challenge_id}:{otp}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()
