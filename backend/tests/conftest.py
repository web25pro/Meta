"""Pytest configuration and fixtures"""
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings

from app.core.security import create_access_token, hash_password
from app.models import User, UserRole, UserType

# Test database URL (use separate test database)
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/lpanda_db", "/lpanda_test_db")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        # Start a transaction
        async with session.begin():
            yield session
            # Rollback happens automatically when exiting the context


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session override"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
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
