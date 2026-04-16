"""
SANJAYA Authentication Module
Handles user registration, login, JWT token generation, and password encryption.
Production-safe implementation using bcrypt and python-jose.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy import create_engine, Column, String, DateTime, Integer, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ── Configuration ────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@sanjaya.local")

# ── Password hashing context ────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Database setup ──────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sanjaya_user:Sanjaya2026!@localhost:5432/sanjaya_db"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ── Security schemes ────────────────────────────────────────────────────
security = HTTPBearer()


# ── Models ──────────────────────────────────────────────────────────────
class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Integer, default=0)  # 1 for admin, 0 for regular user
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


# Create tables
Base.metadata.create_all(bind=engine)


# ── Pydantic schemas ────────────────────────────────────────────────────
class UserRegister(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user_email: str
    is_admin: bool


class TokenData(BaseModel):
    email: Optional[str] = None
    is_admin: bool = False


# ── Password utilities ──────────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT utilities ──────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """Verify JWT token and extract claims."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        is_admin: bool = payload.get("is_admin", False)
        if email is None:
            return None
        return TokenData(email=email, is_admin=is_admin)
    except JWTError:
        return None


# ── Database operations ────────────────────────────────────────────────
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_email(email: str, db=None):
    """Fetch user from database by email."""
    if db is None:
        db = SessionLocal()
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, email, hashed_password, is_admin FROM users WHERE email = :email"),
                {"email": email}
            )
            row = result.fetchone()
            if row:
                return {
                    "id": row[0],
                    "email": row[1],
                    "hashed_password": row[2],
                    "is_admin": bool(row[3])
                }
    except Exception as e:
        print(f"[AUTH] Database error: {e}")
    return None


def create_user(email: str, hashed_password: str, is_admin: int = 0):
    """Create a new user in the database."""
    try:
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO users (email, hashed_password, is_admin, created_at)
                    VALUES (:email, :hashed_password, :is_admin, :created_at)
                """),
                {
                    "email": email,
                    "hashed_password": hashed_password,
                    "is_admin": is_admin,
                    "created_at": datetime.utcnow()
                }
            )
            conn.commit()
            return True
    except Exception as e:
        print(f"[AUTH] Error creating user: {e}")
        return False


def update_last_login(email: str):
    """Update user's last login timestamp."""
    try:
        with engine.connect() as conn:
            conn.execute(
                text("UPDATE users SET last_login = :last_login WHERE email = :email"),
                {"last_login": datetime.utcnow(), "email": email}
            )
            conn.commit()
    except Exception as e:
        print(f"[AUTH] Error updating last login: {e}")


# ── Authentication dependency ──────────────────────────────────────────
async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)):
    """Dependency to verify JWT token and get current user."""
    token = credentials.credentials
    token_data = verify_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user_by_email(token_data.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Dependency to verify current user is an admin."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# ── Validation utilities ──────────────────────────────────────────────
def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"


def validate_email_format(email: str) -> tuple[bool, str]:
    """Validate email format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, "Valid email"
    return False, "Invalid email format"
