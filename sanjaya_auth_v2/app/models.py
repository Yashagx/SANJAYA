import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "auth_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), unique=True, index=True, nullable=False)
    email_encrypted = Column(Text, nullable=False)
    email_hash = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    google_sub = Column(String(128), unique=True, nullable=True)
    role = Column(String(16), default="user", nullable=False)  # user | manager | admin
    mfa_enabled = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    mfa_challenges = relationship("MFAChallenge", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "auth_refresh_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("auth_users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")


class MFAChallenge(Base):
    __tablename__ = "auth_mfa_challenges"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("auth_users.id"), nullable=False, index=True)
    code_hash = Column(String(64), nullable=False)
    purpose = Column(String(24), default="login", nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    consumed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="mfa_challenges")


class AuditLog(Base):
    __tablename__ = "auth_audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    username = Column(String(64), nullable=True)
    action = Column(String(64), nullable=False, index=True)
    detail = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    status = Column(String(16), default="success", nullable=False)  # success | failure
