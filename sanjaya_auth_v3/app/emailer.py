import logging
import smtplib
from email.mime.text import MIMEText

from .config import settings


logger = logging.getLogger("auth.email")


def send_mfa_code_email(to_email: str, otp: str) -> bool:
    subject = "SANJAYA MFA Verification Code"
    body = (
        "Your SANJAYA verification code is: "
        f"{otp}\n\n"
        "This code expires in 5 minutes."
    )

    if settings.mfa_delivery_mode.lower() == "log":
        logger.info("MFA OTP for %s: %s", to_email, otp)
        return True

    if not settings.smtp_host:
        logger.warning("SMTP_HOST not configured. Cannot send MFA email.")
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.smtp_sender
    msg["To"] = to_email

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.smtp_sender, [to_email], msg.as_string())
        return True
    except Exception:
        logger.exception("Failed to send MFA email to %s", to_email)
        return False
