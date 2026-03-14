import resend
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

def _mask_email(email:str) -> str:
    try:
        name, domain = email.split("@", 1)
        if not name:
            return f"***@{domain}"
        return f"{name[0]}***@{domain}"
    except Exception:
        return "***"

def send_password_reset_email(to_email: str, reset_token: str) -> Optional[dict]:
    frontend_base = (settings.FRONTEND_URL).rstrip("/")
    reset_link = f"{frontend_base}/reset-password#token={reset_token}"

    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY is not set. Skipping password reset email send.")
        return None
    
    resend.api_key = settings.RESEND_API_KEY
    

    html_content = f"""
    <p>You requested a password reset.</p>
    <p>Click the link below to reset your password:</p>
    <p><a href="{reset_link}" target="_blank" rel="noopener noreferrer">Reset Password</a></p>
    <p>If you did not request this, you can ignore this email.</p>
    """

    text_content = (
        "You requested a password reset.\n"
        f"Reset link: {reset_link}\n\n"
        "If you did not request this, you can ignore this email."
    )

    params = {
        "from": settings.RESEND_FROM_EMAIL.strip(),
        "to": [to_email],
        "subject": "Password Reset Request",
        "html": html_content,
        "text": text_content
    }
    
    try:
        response = resend.Emails.send(params)
        logger.info("Password reset email sent to %s", _mask_email(to_email))
        return response
    except Exception as e:
        logger.exception("Failed to send password reset email to %s: %s", _mask_email(to_email), str(e))
        return None
