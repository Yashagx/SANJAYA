import os
from dataclasses import dataclass


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("AUTH_APP_NAME", "SANJAYA Auth Service")
    environment: str = os.getenv("AUTH_ENV", "production")

    # Default: SQLite (zero setup). Switch to Postgres by setting AUTH_DATABASE_URL.
    database_url: str = os.getenv(
        "AUTH_DATABASE_URL",
        "sqlite:///./sanjaya_auth.db",
    )

    jwt_secret_key: str = os.getenv("AUTH_JWT_SECRET_KEY", "change-me-please")
    jwt_algorithm: str = os.getenv("AUTH_JWT_ALGORITHM", "HS256")
    access_token_minutes: int = int(os.getenv("AUTH_ACCESS_TOKEN_MINUTES", "15"))
    refresh_token_days: int = int(os.getenv("AUTH_REFRESH_TOKEN_DAYS", "7"))

    pii_encryption_key: str = os.getenv("PII_ENCRYPTION_KEY", "")
    pii_hash_salt: str = os.getenv("PII_HASH_SALT", "change-me-pii-hash-salt")

    mfa_code_ttl_seconds: int = int(os.getenv("MFA_CODE_TTL_SECONDS", "300"))
    mfa_max_attempts: int = int(os.getenv("MFA_MAX_ATTEMPTS", "5"))
    debug_otp_in_response: bool = _as_bool(os.getenv("DEBUG_OTP_IN_RESPONSE", "false"), False)
    mfa_delivery_mode: str = os.getenv("MFA_DELIVERY_MODE", "log")

    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_use_tls: bool = _as_bool(os.getenv("SMTP_USE_TLS", "true"), True)
    smtp_sender: str = os.getenv("SMTP_SENDER", "no-reply@sanjaya.local")

    post_login_redirect_url: str = os.getenv(
        "POST_LOGIN_REDIRECT_URL", "http://16.112.128.251:8000/dashboard#"
    )


settings = Settings()
