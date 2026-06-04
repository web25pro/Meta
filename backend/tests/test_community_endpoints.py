import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskCategory, DifficultyLevel
from app.models.user import User, UserRole, UserType
from app.core.security import hash_password


@pytest.mark.asyncio
async def test_register_community_user(client: AsyncClient, db_session: AsyncSession):
    response = await client.post(
        "/api/v1/community/register",
        json={
            "email": "community_test@example.com",
            "password": "StrongPass123",
            "username": "community_test_user",
            "referral_code": None
        }
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["email"] == "community_test@example.com"
    assert payload["username"] == "community_test_user"
    assert payload["email_verified"] is False
    assert isinstance(payload["referral_code"], str)
    assert len(payload["referral_code"]) == 8
    assert payload["points"] == 0.0

    user = await db_session.get(User, uuid.UUID(payload["id"]))
    assert user is not None
    assert user.email == "community_test@example.com"
    assert user.user_type == UserType.COMMUNITY_USER
    assert user.role == UserRole.COMMUNITY_USER


@pytest.mark.asyncio
async def test_list_public_tasks_returns_visible_tasks(client: AsyncClient, db_session: AsyncSession, admin_user: User):
    task = Task(
        title="Community Challenge",
        description="Complete a short community engagement exercise.",
        assigned_to_group="All",
        deadline=datetime.utcnow() + timedelta(days=7),
        point_value=25.0,
        created_by_id=admin_user.id,
        is_public=True,
        category=TaskCategory.COMMUNITY_ENGAGEMENT,
        max_submissions=100,
        current_submissions=0,
        is_active=True,
        featured=True,
        difficulty_level=DifficultyLevel.EASY,
        estimated_time_minutes=15,
    )
    db_session.add(task)
    await db_session.flush()

    response = await client.get("/api/v1/community/tasks")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["page"] == 1
    assert payload["tasks"][0]["id"] == str(task.id)
    assert payload["tasks"][0]["category"] == TaskCategory.COMMUNITY_ENGAGEMENT.value


@pytest.mark.asyncio
async def test_submit_public_task_requires_verified_email_and_accepts_uploads(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User
):
    # Create public task
    task = Task(
        title="Upload Proof Task",
        description="Submit a proof file for the task.",
        assigned_to_group="All",
        deadline=datetime.utcnow() + timedelta(days=7),
        point_value=10.0,
        created_by_id=admin_user.id,
        is_public=True,
        category=TaskCategory.SURVEYS,
        max_submissions=10,
        current_submissions=0,
        is_active=True,
        featured=False,
        difficulty_level=DifficultyLevel.MEDIUM,
        estimated_time_minutes=30,
    )
    db_session.add(task)
    await db_session.flush()

    # Register and verify community user
    register_response = await client.post(
        "/api/v1/community/register",
        json={
            "email": "verified_community@example.com",
            "password": "StrongPass123",
            "username": "verified_user",
            "referral_code": None
        }
    )
    assert register_response.status_code == 201
    user_payload = register_response.json()
    user = await db_session.get(User, uuid.UUID(user_payload["id"]))
    assert user is not None
    user.email_verified = True
    await db_session.commit()

    login_response = await client.post(
        "/api/v1/community/login",
        json={
            "email": "verified_community@example.com",
            "password": "StrongPass123"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        f"/api/v1/community/tasks/{task.id}/submit",
        headers=headers,
        data={"content": "I have completed the community challenge and attached proof."},
        files={
            "files": (
                "proof.txt",
                b"Proof of completion.",
                "text/plain"
            )
        }
    )

    assert response.status_code == 201
    submission_payload = response.json()
    assert submission_payload["task_id"] == str(task.id)
    assert submission_payload["status"] == "Pending"
    assert submission_payload["content"].startswith("I have completed")
    assert isinstance(submission_payload["id"], str)
