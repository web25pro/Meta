"""SMTP-based email utilities for the LPanda backend."""
from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def build_email_message(
    subject: str,
    to_email: str,
    html_body: str,
    text_body: Optional[str] = None,
    from_email: str = None,
) -> EmailMessage:
    """Build an email message object."""
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_email or settings.EMAIL_FROM
    message["To"] = to_email
    message.set_content(text_body or html_body)
    message.add_alternative(html_body, subtype="html")
    return message


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> None:
    """Send an email message using configured SMTP settings."""
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP is not fully configured, skipping email send")
        return

    message = build_email_message(
        subject=subject,
        to_email=to_email,
        html_body=html_body,
        text_body=text_body,
        from_email=settings.EMAIL_FROM,
    )

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
            logger.info("Email sent", extra={"to": to_email, "subject": subject})
    except Exception as exc:
        logger.error("Failed to send email", extra={"to": to_email, "subject": subject, "error": str(exc)})
        raise


def build_verification_link(token: str) -> str:
    return f"{settings.SITE_BASE_URL}/verify-email?token={token}"


def build_password_reset_link(token: str) -> str:
    return f"{settings.SITE_BASE_URL}/reset-password?token={token}"


async def send_verification_email(to_email: str, token: str) -> None:
    """Send an account verification email."""
    verification_url = build_verification_link(token)
    subject = "Verify your LPanda account"
    text_body = (
        f"Welcome to LPanda!\n\n"
        f"Please verify your email by clicking the link below:\n{verification_url}\n\n"
        "If you did not create an account, please ignore this message."
    )
    html_body = (
        f"<p>Welcome to LPanda!</p>"
        f"<p>Please verify your email by clicking the button below:</p>"
        f"<p><a href=\"{verification_url}\">Verify Email</a></p>"
        f"<p>If you did not create an account, please ignore this message.</p>"
    )
    send_email(to_email=to_email, subject=subject, html_body=html_body, text_body=text_body)


async def send_password_reset_email(to_email: str, token: str) -> None:
    """Send a password reset email."""
    reset_url = build_password_reset_link(token)
    subject = "Reset your LPanda password"
    text_body = (
        f"We received a request to reset your password.\n\n"
        f"Reset your password using the link below:\n{reset_url}\n\n"
        "If you did not request a password reset, please ignore this message."
    )
    html_body = (
        f"<p>We received a request to reset your password.</p>"
        f"<p>Reset your password by clicking the button below:</p>"
        f"<p><a href=\"{reset_url}\">Reset Password</a></p>"
        f"<p>If you did not request a password reset, please ignore this message.</p>"
    )
    send_email(to_email=to_email, subject=subject, html_body=html_body, text_body=text_body)
