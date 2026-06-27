"""Bootstrap / promote an admin (one-time, run on the server).

This is the *only* way to mint the first Overall_Admin — every promotion after
that is done in-app via the admin panel (PATCH /api/v1/admin/users/{id}).
Deliberately a CLI, never an HTTP endpoint, so it can't be reached remotely.

Usage:
    # Promote an existing user to Overall_Admin
    python -m scripts.create_admin --email founder@example.com

    # Create a brand-new admin account
    python -m scripts.create_admin --email founder@example.com \
        --password 'Str0ngPassw0rd!' --username founder

    # Promote to a different role
    python -m scripts.create_admin --email x@y.com --role Ambassador_Admin
"""
import argparse
import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models import User, UserRole, UserType


async def run(email: str, password: str | None, username: str | None, role: str) -> int:
    try:
        target_role = UserRole(role)
    except ValueError:
        valid = ", ".join(r.value for r in UserRole)
        print(f"✗ Invalid role '{role}'. Valid roles: {valid}")
        return 1

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()

        if user:
            user.role = target_role
            user.is_active = True
            user.email_verified = True
            action = "promoted"
        else:
            if not password:
                print(f"✗ No user with {email}. Pass --password to create one.")
                return 1
            user = User(
                name=username or email.split("@")[0],
                email=email,
                username=username or f"admin_{uuid.uuid4().hex[:6]}",
                password_hash=hash_password(password),
                role=target_role,
                user_type=UserType.COMMUNITY_USER,
                email_verified=True,
                is_active=True,
            )
            db.add(user)
            action = "created"

        await db.commit()
        await db.refresh(user)

    print(f"✓ {action}: {user.email} (username={user.username}) is now {user.role.value}")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description="Create or promote an admin user.")
    p.add_argument("--email", required=True)
    p.add_argument("--password", default=None, help="Required only when creating a new user")
    p.add_argument("--username", default=None)
    p.add_argument("--role", default=UserRole.OVERALL_ADMIN.value)
    args = p.parse_args()
    raise SystemExit(asyncio.run(run(args.email, args.password, args.username, args.role)))


if __name__ == "__main__":
    main()
