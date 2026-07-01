"""Startup admin bootstrap.

If BOOTSTRAP_ADMIN_EMAIL is configured, ensure that user exists and is an
Overall_Admin on app startup. Idempotent and failure-tolerant — a DB hiccup
must never crash boot. Remove the env var once the admin exists.
"""
import uuid

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.core.security import hash_password
from app.models import User, UserRole, UserType

logger = get_logger(__name__)


async def ensure_bootstrap_admin() -> None:
    email = (settings.BOOTSTRAP_ADMIN_EMAIL or "").strip().lower()
    if not email:
        return

    try:
        async with AsyncSessionLocal() as db:
            user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()

            if user:
                if user.role != UserRole.OVERALL_ADMIN:
                    user.role = UserRole.OVERALL_ADMIN
                    user.is_active = True
                    user.email_verified = True
                    await db.commit()
                    logger.info("Bootstrap: promoted existing user to Overall_Admin", extra={"email": email})
                else:
                    logger.info("Bootstrap: admin already present", extra={"email": email})
                return

            password = settings.BOOTSTRAP_ADMIN_PASSWORD
            if not password:
                logger.warning(
                    "Bootstrap: no user for BOOTSTRAP_ADMIN_EMAIL and no BOOTSTRAP_ADMIN_PASSWORD set; skipping",
                    extra={"email": email},
                )
                return

            db.add(User(
                name=settings.BOOTSTRAP_ADMIN_USERNAME or email.split("@")[0],
                email=email,
                username=settings.BOOTSTRAP_ADMIN_USERNAME or f"admin_{uuid.uuid4().hex[:6]}",
                password_hash=hash_password(password),
                role=UserRole.OVERALL_ADMIN,
                user_type=UserType.COMMUNITY_USER,
                email_verified=True,
                is_active=True,
            ))
            await db.commit()
            logger.info("Bootstrap: created Overall_Admin", extra={"email": email})
    except Exception as exc:  # never block startup
        logger.error("Bootstrap admin failed", extra={"error": str(exc)})
