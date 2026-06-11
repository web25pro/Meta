"""Tests for user registration"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, UserRole, UserType
from app.main import app


@pytest.mark.asyncio
async def test_public_registration_user_role(db_session: AsyncSession, client: AsyncClient):
    """Test that a public user can register with the 'USER' role"""
    registration_data = {
        "name": "Public User",
        "email": "public@example.com",
        "password": "SecurePassword123!",
        "role": "User",
        "user_type": "User"
    }
    
    response = await client.post("/api/v1/users", json=registration_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Public User"
    assert data["email"] == "public@example.com"
    assert data["role"] == "User"
    assert data["user_type"] == "User"
    
    # Verify in database
    result = await db_session.execute(
        select(User).where(User.email == "public@example.com")
    )
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.role == UserRole.USER
    assert user.user_type == UserType.USER


@pytest.mark.asyncio
async def test_public_registration_restricted_roles(db_session: AsyncSession, client: AsyncClient):
    """Test that a public user cannot register with admin or team roles"""
    registration_data = {
        "name": "Hacker",
        "email": "hacker@example.com",
        "password": "SecurePassword123!",
        "role": "Overall_Admin",
        "user_type": "Team_Member"
    }
    
    response = await client.post("/api/v1/users", json=registration_data)
    
    assert response.status_code == 403
    data = response.json()
    error_message = data["error"]["message"] if "error" in data else data["detail"]
    assert "Public registration is only allowed for 'USER' role" in error_message


@pytest.mark.asyncio
async def test_admin_can_still_create_any_user(db_session: AsyncSession, client: AsyncClient, admin_token_headers):
    """Test that an admin can still create any user type via the same endpoint"""
    registration_data = {
        "name": "New Team Member",
        "email": "newteam@example.com",
        "password": "SecurePassword123!",
        "role": "Team_Member",
        "user_type": "Team_Member"
    }
    
    response = await client.post(
        "/api/v1/users", 
        json=registration_data,
        headers=admin_token_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "Team_Member"
    assert data["user_type"] == "Team_Member"
