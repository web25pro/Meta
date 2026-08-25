"""Resend-based email utilities for the LPanda backend."""
from typing import Optional
import resend

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailDeliveryError(RuntimeError):
    """Raised when verification email cannot be handed to the provider."""


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> None:
    """Send an email message using Resend SDK."""
    if not settings.RESEND_API_KEY:
        raise EmailDeliveryError("Email delivery is not configured")

    resend.api_key = settings.RESEND_API_KEY

    from_email = settings.EMAIL_FROM
    if not from_email or "@" not in from_email:
        raise EmailDeliveryError("EMAIL_FROM must be a verified Resend sender address")
        
    # Format as 'Name <email@domain.com>' which Resend prefers
    formatted_from = f"LPanda Platform <{from_email}>" if "<" not in from_email else from_email

    try:
        params = {
            "from": formatted_from,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }
        if text_body:
            params["text"] = text_body

        response = resend.Emails.send(params)
        logger.info("Email sent via Resend", extra={"to": to_email, "subject": subject, "id": response.get("id")})
    except Exception as exc:
        logger.exception("Failed to send email via Resend", extra={"to": to_email, "subject": subject})
        raise EmailDeliveryError("Email provider rejected the message") from exc


def build_password_reset_link(token: str) -> str:
    base_url = settings.SITE_BASE_URL.rstrip('/')
    return f"{base_url}/auth/password-reset-confirm?token={token}"


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
