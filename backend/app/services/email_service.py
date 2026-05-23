"""
Email service using Resend.
Handles: email verification, password reset, invite notifications.
"""
import logging
from typing import Optional

import resend

from app.config import settings

logger = logging.getLogger(__name__)


def _is_configured() -> bool:
    return bool(settings.RESEND_API_KEY)


def _init_resend():
    resend.api_key = settings.RESEND_API_KEY


# ── Templates ─────────────────────────────────────────────────────────────────

def _verification_html(verify_url: str, name: Optional[str] = None) -> str:
    greeting = f"Hi {name}," if name else "Hi,"
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f0; margin: 0; padding: 40px 0; }}
    .card {{ background: #fff; max-width: 520px; margin: 0 auto; border-radius: 16px; padding: 40px 48px; box-shadow: 0 2px 12px rgba(0,0,0,.08); }}
    .logo {{ font-size: 20px; font-weight: 700; color: #1e1c19; margin-bottom: 32px; }}
    .logo span {{ color: #c8602a; }}
    h1 {{ font-size: 22px; color: #1e1c19; margin: 0 0 12px; }}
    p {{ color: #555; line-height: 1.6; margin: 0 0 24px; }}
    .btn {{ display: inline-block; background: #c8602a; color: #fff; text-decoration: none; padding: 14px 32px; border-radius: 10px; font-weight: 600; font-size: 15px; }}
    .note {{ font-size: 13px; color: #999; margin-top: 24px; }}
    .url {{ word-break: break-all; font-size: 13px; color: #999; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">vspomin<span>.ai</span></div>
    <h1>Confirm your email</h1>
    <p>{greeting}<br>Click the button below to verify your email address and activate your account.</p>
    <a href="{verify_url}" class="btn">Verify Email</a>
    <p class="note">This link expires in 24 hours. If you didn't create an account, you can ignore this email.</p>
    <p class="url">{verify_url}</p>
  </div>
</body>
</html>
"""


def _password_reset_html(reset_url: str, name: Optional[str] = None) -> str:
    greeting = f"Hi {name}," if name else "Hi,"
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f0; margin: 0; padding: 40px 0; }}
    .card {{ background: #fff; max-width: 520px; margin: 0 auto; border-radius: 16px; padding: 40px 48px; box-shadow: 0 2px 12px rgba(0,0,0,.08); }}
    .logo {{ font-size: 20px; font-weight: 700; color: #1e1c19; margin-bottom: 32px; }}
    .logo span {{ color: #c8602a; }}
    h1 {{ font-size: 22px; color: #1e1c19; margin: 0 0 12px; }}
    p {{ color: #555; line-height: 1.6; margin: 0 0 24px; }}
    .btn {{ display: inline-block; background: #c8602a; color: #fff; text-decoration: none; padding: 14px 32px; border-radius: 10px; font-weight: 600; font-size: 15px; }}
    .note {{ font-size: 13px; color: #999; margin-top: 24px; }}
    .url {{ word-break: break-all; font-size: 13px; color: #999; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">vspomin<span>.ai</span></div>
    <h1>Reset your password</h1>
    <p>{greeting}<br>We received a request to reset your password. Click the button below to choose a new one.</p>
    <a href="{reset_url}" class="btn">Reset Password</a>
    <p class="note">This link expires in 1 hour. If you didn't request a password reset, you can ignore this email — your password will not be changed.</p>
    <p class="url">{reset_url}</p>
  </div>
</body>
</html>
"""


# ── Public API ─────────────────────────────────────────────────────────────────

def send_verification_email(to_email: str, token: str, name: Optional[str] = None) -> bool:
    """
    Send email verification link.
    Returns True on success, False if not configured or on error.
    """
    if not _is_configured():
        logger.warning("RESEND_API_KEY not set — skipping verification email for %s", to_email)
        logger.info("Verification URL (dev): %s/verify-email?token=%s", settings.FRONTEND_URL, token)
        return False

    _init_resend()
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    try:
        resend.Emails.send({
            "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
            "to": [to_email],
            "subject": "Confirm your email — vspomin.ai",
            "html": _verification_html(verify_url, name),
        })
        logger.info("Verification email sent to %s", to_email)
        return True
    except Exception as exc:
        logger.error("Failed to send verification email to %s: %s", to_email, exc)
        return False


def send_password_reset_email(to_email: str, token: str, name: Optional[str] = None) -> bool:
    """
    Send password reset link.
    Returns True on success, False if not configured or on error.
    """
    if not _is_configured():
        logger.warning("RESEND_API_KEY not set — skipping password reset email for %s", to_email)
        logger.info("Reset URL (dev): %s/reset-password?token=%s", settings.FRONTEND_URL, token)
        return False

    _init_resend()
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    try:
        resend.Emails.send({
            "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
            "to": [to_email],
            "subject": "Reset your password — vspomin.ai",
            "html": _password_reset_html(reset_url, name),
        })
        logger.info("Password reset email sent to %s", to_email)
        return True
    except Exception as exc:
        logger.error("Failed to send password reset email to %s: %s", to_email, exc)
        return False
