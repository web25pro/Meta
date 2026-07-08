"""Reset the bootstrap admin password.

Run on Render shell:
    cd backend && python -m scripts.reset_admin_password

Reads BOOTSTRAP_ADMIN_EMAIL and a new password from input,
then updates the password hash in the database.
"""
import asyncio
import getpass

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.core.config import settings
from app.models import User


async def reset_password():
    email = (settings.BOOTSTRAP_ADMIN_EMAIL or "").strip().lower()
    if not email:
        print("ERROR: BOOTSTRAP_ADMIN_EMAIL is not set in environment.")
        return

    new_password = getpass.getpass(f"New password for {email}: ")
    if not new_password or len(new_password) < 8:
        print("ERROR: Password must be at least 8 characters.")
        return

    confirm = getpass.getpass("Confirm password: ")
    if new_password != confirm:
        print("ERROR: Passwords do not match.")
        return

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if not user:
            print(f"ERROR: No user found with email {email}")
            return

        user.password_hash = hash_password(new_password)
        await db.commit()
        print(f"SUCCESS: Password updated for {email}")


if __name__ == "__main__":
    asyncio.run(reset_password())
