"""
Script to create an admin user for the LPanda platform.

Usage:
    python scripts/create_admin.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.core.database import Base


async def create_admin_user():
    """Create an admin user in the database."""
    
    # Create database engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if admin already exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.email == "admin@lpanda.com")
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print("❌ Admin user already exists!")
            print(f"   Email: admin@lpanda.com")
            return
        
        # Create admin user
        admin_user = User(
            email="admin@lpanda.com",
            hashed_password=hash_password("Admin123!"),
            full_name="System Administrator",
            role="Overall_Admin",
            user_type="Team_Member",
            is_active=True,
        )
        
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print(f"   Email: admin@lpanda.com")
        print(f"   Password: Admin123!")
        print(f"   Role: Overall_Admin")
        print(f"   User ID: {admin_user.id}")
        print("\n⚠️  Please change the password after first login!")
    
    await engine.dispose()


async def create_test_users():
    """Create test users for development."""
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        from sqlalchemy import select
        
        test_users = [
            {
                "email": "ambassador_admin@lpanda.com",
                "password": "Ambassador123!",
                "full_name": "Ambassador Admin",
                "role": "Ambassador_Admin",
                "user_type": "Ambassador",
            },
            {
                "email": "team_member@lpanda.com",
                "password": "TeamMember123!",
                "full_name": "Test Team Member",
                "role": "Team_Member",
                "user_type": "Team_Member",
            },
            {
                "email": "ambassador@lpanda.com",
                "password": "Ambassador123!",
                "full_name": "Test Ambassador",
                "role": "Ambassador",
                "user_type": "Ambassador",
            },
        ]
        
        created_count = 0
        for user_data in test_users:
            # Check if user exists
            result = await session.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                user = User(
                    email=user_data["email"],
                    hashed_password=hash_password(user_data["password"]),
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    user_type=user_data["user_type"],
                    is_active=True,
                )
                session.add(user)
                created_count += 1
        
        if created_count > 0:
            await session.commit()
            print(f"\n✅ Created {created_count} test users!")
            print("\nTest User Credentials:")
            print("=" * 60)
            for user_data in test_users:
                print(f"Email: {user_data['email']}")
                print(f"Password: {user_data['password']}")
                print(f"Role: {user_data['role']}")
                print("-" * 60)
        else:
            print("\n✅ All test users already exist!")
    
    await engine.dispose()


async def main():
    """Main function."""
    print("=" * 60)
    print("LPanda Platform - Admin User Creation")
    print("=" * 60)
    print()
    
    # Create admin user
    await create_admin_user()
    
    # Ask if user wants to create test users
    print("\nDo you want to create test users for development? (y/n): ", end="")
    try:
        response = input().strip().lower()
        if response == 'y':
            await create_test_users()
    except:
        pass
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
