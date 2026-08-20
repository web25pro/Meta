"""Pytest configuration and fixtures"""
import asyncio
import uuid
import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings

from app.core.security import create_access_token, hash_password
from app.models import User, UserRole, UserType

# Tests run in an isolated schema, not in ``public``. The old string-replace
# approach silently reused the configured database whenever its name was not
# literally ``lpanda_db`` (for example a managed Postgres ``postgres`` DB).
TEST_DATABASE_URL = settings.DATABASE_URL
TEST_SCHEMA = f"test_{uuid.uuid4().hex}"


async def _truncate(session: AsyncSession) -> None:
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    await session.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
    await session.commit()

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    admin_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with admin_engine.begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA {TEST_SCHEMA}"))

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
        connect_args={"server_settings": {"search_path": f"{TEST_SCHEMA},public"}},
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()
    async with admin_engine.begin() as conn:
        await conn.execute(text(f"DROP SCHEMA {TEST_SCHEMA} CASCADE"))
    await admin_engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        await _truncate(session)
        try:
            yield session
        finally:
            await session.rollback()
            await _truncate(session)


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session override"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user for testing"""
    user = User(
        name="Admin User",
        email="admin_test@example.com",
        password_hash=hash_password("AdminPassword123!"),
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def admin_token_headers(admin_user: User) -> dict[str, str]:
    """Get auth headers for admin user"""
    access_token = create_access_token(
        user_id=str(admin_user.id),
        role=admin_user.role.value,
        user_type=admin_user.user_type.value
    )
    return {"Authorization": f"Bearer {access_token}"}
