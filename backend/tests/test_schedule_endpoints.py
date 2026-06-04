"""Tests for schedule API endpoints"""
import pytest
import uuid
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole, UserType, Schedule
from app.models.leaderboard_schedule_announcement import TargetGroup
from app.core.security import hash_password, create_access_token


@pytest.fixture
async def overall_admin(db_session: AsyncSession):
    """Create Overall_Admin test user"""
    user = User(
        id=uuid.uuid4(),
        name="Overall Admin",
        email="overall_admin@test.com",
        password_hash=hash_password("password123"),
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def ambassador_admin(db_session: AsyncSession):
    """Create Ambassador_Admin test user"""
    user = User(
        id=uuid.uuid4(),
        name="Ambassador Admin",
        email="ambassador_admin@test.com",
        password_hash=hash_password("password123"),
        role=UserRole.AMBASSADOR_ADMIN,
        user_type=UserType.AMBASSADOR,
        points=0.0
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def team_member(db_session: AsyncSession):
    """Create Team_Member test user"""
    user = User(
        id=uuid.uuid4(),
        name="Team Member",
        email="team_member@test.com",
        password_hash=hash_password("password123"),
        role=UserRole.TEAM_MEMBER,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def ambassador(db_session: AsyncSession):
    """Create Ambassador test user"""
    user = User(
        id=uuid.uuid4(),
        name="Ambassador",
        email="ambassador@test.com",
        password_hash=hash_password("password123"),
        role=UserRole.AMBASSADOR,
        user_type=UserType.AMBASSADOR,
        points=0.0
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def create_auth_token(user: User) -> str:
    """Create authentication token for user"""
    return create_access_token(
        user_id=str(user.id),
        role=user.role.value,
        user_type=user.user_type.value
    )


# Test Requirement 7.2: Overall_Admin can create schedules for any target_group
@pytest.mark.asyncio
async def test_overall_admin_create_schedule_for_team_members(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """Test Overall_Admin can create schedule for Team_Members"""
    token = create_auth_token(overall_admin)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "title": "Team Meeting",
        "description": "Weekly team sync meeting",
        "event_date": event_date.isoformat(),
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify response structure
    assert "id" in data
    assert data["title"] == schedule_data["title"]
    assert data["description"] == schedule_data["description"]
    assert data["target_group"] == "Team_Members"
    assert data["created_by_id"] == str(overall_admin.id)
    
    # Verify schedule was created in database
    from sqlalchemy import select
    result = await db_session.execute(
        select(Schedule).where(Schedule.id == uuid.UUID(data["id"]))
    )
    schedule = result.scalar_one_or_none()
    assert schedule is not None
    assert schedule.target_group == TargetGroup.TEAM_MEMBERS


@pytest.mark.asyncio
async def test_overall_admin_create_schedule_for_ambassadors(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """Test Overall_Admin can create schedule for Ambassadors"""
    token = create_auth_token(overall_admin)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "title": "Ambassador Training",
        "description": "Monthly ambassador training session",
        "event_date": event_date.isoformat(),
        "target_group": "Ambassadors"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["target_group"] == "Ambassadors"
    assert data["created_by_id"] == str(overall_admin.id)
    
    # Verify schedule was created in database
    from sqlalchemy import select
    result = await db_session.execute(
        select(Schedule).where(Schedule.id == uuid.UUID(data["id"]))
    )
    schedule = result.scalar_one_or_none()
    assert schedule is not None
    assert schedule.target_group == TargetGroup.AMBASSADORS


@pytest.mark.asyncio
async def test_overall_admin_create_schedule_for_all(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """Test Overall_Admin can create schedule for All"""
    token = create_auth_token(overall_admin)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "title": "Company All-Hands",
        "description": "Quarterly all-hands meeting",
        "event_date": event_date.isoformat(),
        "target_group": "All"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["target_group"] == "All"
    assert data["created_by_id"] == str(overall_admin.id)
    
    # Verify schedule was created in database
    from sqlalchemy import select
    result = await db_session.execute(
        select(Schedule).where(Schedule.id == uuid.UUID(data["id"]))
    )
    schedule = result.scalar_one_or_none()
    assert schedule is not None
    assert schedule.target_group == TargetGroup.ALL


# Test Requirement 7.3: Ambassador_Admin can only create schedules for Ambassadors or All
@pytest.mark.asyncio
async def test_ambassador_admin_create_schedule_for_ambassadors(
    client: AsyncClient,
    db_session: AsyncSession,
    ambassador_admin
):
    """Test Ambassador_Admin can create schedule for Ambassadors"""
    token = create_auth_token(ambassador_admin)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "title": "Ambassador Workshop",
        "description": "Ambassador skill development workshop",
        "event_date": event_date.isoformat(),
        "target_group": "Ambassadors"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["target_group"] == "Ambassadors"
    assert data["created_by_id"] == str(ambassador_admin.id)


@pytest.mark.asyncio
async def test_ambassador_admin_create_schedule_for_all(
    client: AsyncClient,
    db_session: AsyncSession,
    ambassador_admin
):
    """Test Ambassador_Admin can create schedule for All"""
    token = create_auth_token(ambassador_admin)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "title": "General Announcement",
        "description": "Important announcement for everyone",
        "event_date": event_date.isoformat(),
        "target_group": "All"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["target_group"] == "All"
    assert data["created_by_id"] == str(ambassador_admin.id)


@pytest.mark.asyncio
async def test_ambassador_admin_cannot_create_schedule_for_team_members(
    client: AsyncClient,
    ambassador_admin
):
    """Test Ambassador_Admin cannot create schedule for Team_Members (Requirement 7.3)"""
    token = create_auth_token(ambassador_admin)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "title": "Team Meeting",
        "description": "Team meeting - should fail",
        "event_date": event_date.isoformat(),
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


# Test that non-admin users cannot create schedules
@pytest.mark.asyncio
async def test_team_member_cannot_create_schedule(
    client: AsyncClient,
    team_member
):
    """Test Team_Member cannot create schedules"""
    token = create_auth_token(team_member)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "title": "Unauthorized Schedule",
        "description": "This should fail",
        "event_date": event_date.isoformat(),
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ambassador_cannot_create_schedule(
    client: AsyncClient,
    ambassador
):
    """Test Ambassador cannot create schedules"""
    token = create_auth_token(ambassador)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "title": "Unauthorized Schedule",
        "description": "This should fail",
        "event_date": event_date.isoformat(),
        "target_group": "Ambassadors"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


# Test validation of target_group values (Requirement 7.1)
@pytest.mark.asyncio
async def test_create_schedule_with_invalid_target_group(
    client: AsyncClient,
    overall_admin
):
    """Test schedule creation with invalid target_group value"""
    token = create_auth_token(overall_admin)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "title": "Invalid Schedule",
        "description": "Schedule with invalid target_group",
        "event_date": event_date.isoformat(),
        "target_group": "InvalidGroup"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should fail validation at schema level (422) or business logic level (400)
    assert response.status_code in [400, 422]


# Test required fields validation
@pytest.mark.asyncio
async def test_create_schedule_missing_title(
    client: AsyncClient,
    overall_admin
):
    """Test schedule creation without title"""
    token = create_auth_token(overall_admin)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "description": "Schedule without title",
        "event_date": event_date.isoformat(),
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_schedule_missing_description(
    client: AsyncClient,
    overall_admin
):
    """Test schedule creation without description"""
    token = create_auth_token(overall_admin)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "title": "Schedule without description",
        "event_date": event_date.isoformat(),
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_schedule_missing_event_date(
    client: AsyncClient,
    overall_admin
):
    """Test schedule creation without event_date"""
    token = create_auth_token(overall_admin)
    
    schedule_data = {
        "title": "Schedule without event_date",
        "description": "Missing event_date field",
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_schedule_missing_target_group(
    client: AsyncClient,
    overall_admin
):
    """Test schedule creation without target_group"""
    token = create_auth_token(overall_admin)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "title": "Schedule without target_group",
        "description": "Missing target_group field",
        "event_date": event_date.isoformat()
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


# Test authentication requirements
@pytest.mark.asyncio
async def test_create_schedule_without_authentication(client: AsyncClient):
    """Test schedule creation without authentication token"""
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "title": "Unauthorized Schedule",
        "description": "Should fail without auth",
        "event_date": event_date.isoformat(),
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data
    )
    
    assert response.status_code == 403  # FastAPI HTTPBearer returns 403


@pytest.mark.asyncio
async def test_create_schedule_with_invalid_token(client: AsyncClient):
    """Test schedule creation with invalid authentication token"""
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "title": "Unauthorized Schedule",
        "description": "Should fail with invalid token",
        "event_date": event_date.isoformat(),
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


# Test data persistence
@pytest.mark.asyncio
async def test_schedule_data_persistence(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """Test that all schedule fields are persisted correctly"""
    token = create_auth_token(overall_admin)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "title": "Persistence Test Schedule",
        "description": "Testing data persistence with special characters: @#$%",
        "event_date": event_date.isoformat(),
        "target_group": "All"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Retrieve from database and verify all fields
    from sqlalchemy import select
    result = await db_session.execute(
        select(Schedule).where(Schedule.id == uuid.UUID(data["id"]))
    )
    schedule = result.scalar_one_or_none()
    
    assert schedule is not None
    assert schedule.title == schedule_data["title"]
    assert schedule.description == schedule_data["description"]
    assert schedule.target_group.value == schedule_data["target_group"]
    assert schedule.created_by_id == overall_admin.id
    assert schedule.created_at is not None
    assert schedule.updated_at is not None
    assert schedule.deleted_at is None


# Test edge cases
@pytest.mark.asyncio
async def test_create_schedule_with_past_event_date(
    client: AsyncClient,
    overall_admin
):
    """Test schedule creation with past event_date (should be allowed)"""
    token = create_auth_token(overall_admin)
    event_date = datetime.utcnow() - timedelta(days=7)  # Past date
    
    schedule_data = {
        "title": "Past Event",
        "description": "Event in the past",
        "event_date": event_date.isoformat(),
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Past dates should be allowed (for historical records)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_schedule_with_long_title(
    client: AsyncClient,
    overall_admin
):
    """Test schedule creation with maximum length title"""
    token = create_auth_token(overall_admin)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    # Title max length is 255 characters
    long_title = "A" * 255
    
    schedule_data = {
        "title": long_title,
        "description": "Testing long title",
        "event_date": event_date.isoformat(),
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == long_title


@pytest.mark.asyncio
async def test_create_schedule_with_too_long_title(
    client: AsyncClient,
    overall_admin
):
    """Test schedule creation with title exceeding maximum length"""
    token = create_auth_token(overall_admin)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    # Title max length is 255 characters
    too_long_title = "A" * 256
    
    schedule_data = {
        "title": too_long_title,
        "description": "Testing too long title",
        "event_date": event_date.isoformat(),
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_schedule_with_empty_title(
    client: AsyncClient,
    overall_admin
):
    """Test schedule creation with empty title"""
    token = create_auth_token(overall_admin)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "title": "",
        "description": "Testing empty title",
        "event_date": event_date.isoformat(),
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_schedule_with_empty_description(
    client: AsyncClient,
    overall_admin
):
    """Test schedule creation with empty description"""
    token = create_auth_token(overall_admin)
    event_date = datetime.utcnow() + timedelta(days=7)
    
    schedule_data = {
        "title": "Schedule with empty description",
        "description": "",
        "event_date": event_date.isoformat(),
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/schedules",
        json=schedule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


# ============================================================================
# Tests for Schedule Update Endpoint (Requirement 7.4)
# ============================================================================

@pytest.fixture
async def sample_schedule(db_session: AsyncSession, overall_admin):
    """Create a sample schedule for testing updates and deletes"""
    schedule = Schedule(
        id=uuid.uuid4(),
        title="Sample Schedule",
        description="Sample description for testing",
        event_date=datetime.utcnow() + timedelta(days=7),
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)
    return schedule


@pytest.fixture
async def ambassador_schedule(db_session: AsyncSession, ambassador_admin):
    """Create an ambassador schedule for testing"""
    schedule = Schedule(
        id=uuid.uuid4(),
        title="Ambassador Schedule",
        description="Ambassador event",
        event_date=datetime.utcnow() + timedelta(days=7),
        target_group=TargetGroup.AMBASSADORS,
        created_by_id=ambassador_admin.id
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)
    return schedule


@pytest.mark.asyncio
async def test_overall_admin_update_schedule_title(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    sample_schedule
):
    """Test Overall_Admin can update schedule title"""
    token = create_auth_token(overall_admin)
    
    update_data = {
        "title": "Updated Schedule Title"
    }
    
    response = await client.put(
        f"/api/v1/schedules/{sample_schedule.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == str(sample_schedule.id)
    assert data["title"] == "Updated Schedule Title"
    assert data["description"] == sample_schedule.description  # Unchanged
    assert data["target_group"] == sample_schedule.target_group.value  # Unchanged
    
    # Verify in database
    await db_session.refresh(sample_schedule)
    assert sample_schedule.title == "Updated Schedule Title"


@pytest.mark.asyncio
async def test_overall_admin_update_schedule_description(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    sample_schedule
):
    """Test Overall_Admin can update schedule description"""
    token = create_auth_token(overall_admin)
    
    update_data = {
        "description": "Updated description with new details"
    }
    
    response = await client.put(
        f"/api/v1/schedules/{sample_schedule.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["description"] == "Updated description with new details"
    assert data["title"] == sample_schedule.title  # Unchanged


@pytest.mark.asyncio
async def test_overall_admin_update_schedule_event_date(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    sample_schedule
):
    """Test Overall_Admin can update schedule event_date"""
    token = create_auth_token(overall_admin)
    new_event_date = datetime.utcnow() + timedelta(days=14)
    
    update_data = {
        "event_date": new_event_date.isoformat()
    }
    
    response = await client.put(
        f"/api/v1/schedules/{sample_schedule.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Parse and compare dates (allowing for minor timezone differences)
    response_date = datetime.fromisoformat(data["event_date"].replace('Z', '+00:00'))
    assert abs((response_date - new_event_date).total_seconds()) < 2


@pytest.mark.asyncio
async def test_overall_admin_update_schedule_target_group(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    sample_schedule
):
    """Test Overall_Admin can update schedule target_group"""
    token = create_auth_token(overall_admin)
    
    update_data = {
        "target_group": "Ambassadors"
    }
    
    response = await client.put(
        f"/api/v1/schedules/{sample_schedule.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["target_group"] == "Ambassadors"
    
    # Verify in database
    await db_session.refresh(sample_schedule)
    assert sample_schedule.target_group == TargetGroup.AMBASSADORS


@pytest.mark.asyncio
async def test_overall_admin_update_multiple_fields(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    sample_schedule
):
    """Test Overall_Admin can update multiple schedule fields at once"""
    token = create_auth_token(overall_admin)
    new_event_date = datetime.utcnow() + timedelta(days=30)
    
    update_data = {
        "title": "Completely Updated Schedule",
        "description": "All fields updated",
        "event_date": new_event_date.isoformat(),
        "target_group": "All"
    }
    
    response = await client.put(
        f"/api/v1/schedules/{sample_schedule.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["title"] == "Completely Updated Schedule"
    assert data["description"] == "All fields updated"
    assert data["target_group"] == "All"


@pytest.mark.asyncio
async def test_ambassador_admin_update_ambassador_schedule(
    client: AsyncClient,
    db_session: AsyncSession,
    ambassador_admin,
    ambassador_schedule
):
    """Test Ambassador_Admin can update ambassador schedules"""
    token = create_auth_token(ambassador_admin)
    
    update_data = {
        "title": "Updated Ambassador Event"
    }
    
    response = await client.put(
        f"/api/v1/schedules/{ambassador_schedule.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["title"] == "Updated Ambassador Event"


@pytest.mark.asyncio
async def test_ambassador_admin_cannot_update_to_team_members(
    client: AsyncClient,
    ambassador_admin,
    ambassador_schedule
):
    """Test Ambassador_Admin cannot update schedule target_group to Team_Members"""
    token = create_auth_token(ambassador_admin)
    
    update_data = {
        "target_group": "Team_Members"
    }
    
    response = await client.put(
        f"/api/v1/schedules/{ambassador_schedule.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_team_member_cannot_update_schedule(
    client: AsyncClient,
    team_member,
    sample_schedule
):
    """Test Team_Member cannot update schedules"""
    token = create_auth_token(team_member)
    
    update_data = {
        "title": "Unauthorized Update"
    }
    
    response = await client.put(
        f"/api/v1/schedules/{sample_schedule.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ambassador_cannot_update_schedule(
    client: AsyncClient,
    ambassador,
    sample_schedule
):
    """Test Ambassador cannot update schedules"""
    token = create_auth_token(ambassador)
    
    update_data = {
        "title": "Unauthorized Update"
    }
    
    response = await client.put(
        f"/api/v1/schedules/{sample_schedule.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_nonexistent_schedule(
    client: AsyncClient,
    overall_admin
):
    """Test updating a schedule that doesn't exist"""
    token = create_auth_token(overall_admin)
    nonexistent_id = uuid.uuid4()
    
    update_data = {
        "title": "Update Nonexistent"
    }
    
    response = await client.put(
        f"/api/v1/schedules/{nonexistent_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_schedule_with_invalid_target_group(
    client: AsyncClient,
    overall_admin,
    sample_schedule
):
    """Test updating schedule with invalid target_group"""
    token = create_auth_token(overall_admin)
    
    update_data = {
        "target_group": "InvalidGroup"
    }
    
    response = await client.put(
        f"/api/v1/schedules/{sample_schedule.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_update_schedule_with_empty_title(
    client: AsyncClient,
    overall_admin,
    sample_schedule
):
    """Test updating schedule with empty title"""
    token = create_auth_token(overall_admin)
    
    update_data = {
        "title": ""
    }
    
    response = await client.put(
        f"/api/v1/schedules/{sample_schedule.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_schedule_with_empty_description(
    client: AsyncClient,
    overall_admin,
    sample_schedule
):
    """Test updating schedule with empty description"""
    token = create_auth_token(overall_admin)
    
    update_data = {
        "description": ""
    }
    
    response = await client.put(
        f"/api/v1/schedules/{sample_schedule.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_schedule_without_authentication(
    client: AsyncClient,
    sample_schedule
):
    """Test updating schedule without authentication"""
    update_data = {
        "title": "Unauthorized Update"
    }
    
    response = await client.put(
        f"/api/v1/schedules/{sample_schedule.id}",
        json=update_data
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_schedule_with_invalid_token(
    client: AsyncClient,
    sample_schedule
):
    """Test updating schedule with invalid token"""
    update_data = {
        "title": "Unauthorized Update"
    }
    
    response = await client.put(
        f"/api/v1/schedules/{sample_schedule.id}",
        json=update_data,
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


# ============================================================================
# Tests for Schedule Deletion Endpoint (Requirement 7.4)
# ============================================================================

@pytest.mark.asyncio
async def test_overall_admin_delete_schedule(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    sample_schedule
):
    """Test Overall_Admin can delete schedules"""
    token = create_auth_token(overall_admin)
    schedule_id = sample_schedule.id
    
    response = await client.delete(
        f"/api/v1/schedules/{schedule_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204
    
    # Verify soft delete in database
    await db_session.refresh(sample_schedule)
    assert sample_schedule.deleted_at is not None


@pytest.mark.asyncio
async def test_ambassador_admin_delete_ambassador_schedule(
    client: AsyncClient,
    db_session: AsyncSession,
    ambassador_admin,
    ambassador_schedule
):
    """Test Ambassador_Admin can delete ambassador schedules"""
    token = create_auth_token(ambassador_admin)
    schedule_id = ambassador_schedule.id
    
    response = await client.delete(
        f"/api/v1/schedules/{schedule_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204
    
    # Verify soft delete in database
    await db_session.refresh(ambassador_schedule)
    assert ambassador_schedule.deleted_at is not None


@pytest.mark.asyncio
async def test_ambassador_admin_cannot_delete_team_members_schedule(
    client: AsyncClient,
    db_session: AsyncSession,
    ambassador_admin,
    sample_schedule
):
    """Test Ambassador_Admin cannot delete Team_Members schedules"""
    token = create_auth_token(ambassador_admin)
    
    response = await client.delete(
        f"/api/v1/schedules/{sample_schedule.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()
    
    # Verify schedule was NOT deleted
    await db_session.refresh(sample_schedule)
    assert sample_schedule.deleted_at is None


@pytest.mark.asyncio
async def test_team_member_cannot_delete_schedule(
    client: AsyncClient,
    db_session: AsyncSession,
    team_member,
    sample_schedule
):
    """Test Team_Member cannot delete schedules"""
    token = create_auth_token(team_member)
    
    response = await client.delete(
        f"/api/v1/schedules/{sample_schedule.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()
    
    # Verify schedule was NOT deleted
    await db_session.refresh(sample_schedule)
    assert sample_schedule.deleted_at is None


@pytest.mark.asyncio
async def test_ambassador_cannot_delete_schedule(
    client: AsyncClient,
    db_session: AsyncSession,
    ambassador,
    sample_schedule
):
    """Test Ambassador cannot delete schedules"""
    token = create_auth_token(ambassador)
    
    response = await client.delete(
        f"/api/v1/schedules/{sample_schedule.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()
    
    # Verify schedule was NOT deleted
    await db_session.refresh(sample_schedule)
    assert sample_schedule.deleted_at is None


@pytest.mark.asyncio
async def test_delete_nonexistent_schedule(
    client: AsyncClient,
    overall_admin
):
    """Test deleting a schedule that doesn't exist"""
    token = create_auth_token(overall_admin)
    nonexistent_id = uuid.uuid4()
    
    response = await client.delete(
        f"/api/v1/schedules/{nonexistent_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_already_deleted_schedule(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    sample_schedule
):
    """Test deleting a schedule that's already been deleted"""
    token = create_auth_token(overall_admin)
    
    # First deletion
    response = await client.delete(
        f"/api/v1/schedules/{sample_schedule.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204
    
    # Second deletion attempt
    response = await client.delete(
        f"/api/v1/schedules/{sample_schedule.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_schedule_without_authentication(
    client: AsyncClient,
    sample_schedule
):
    """Test deleting schedule without authentication"""
    response = await client.delete(
        f"/api/v1/schedules/{sample_schedule.id}"
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_schedule_with_invalid_token(
    client: AsyncClient,
    sample_schedule
):
    """Test deleting schedule with invalid token"""
    response = await client.delete(
        f"/api/v1/schedules/{sample_schedule.id}",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_soft_delete_preserves_audit_trail(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    sample_schedule
):
    """Test that soft delete preserves schedule data for audit trail"""
    token = create_auth_token(overall_admin)
    
    # Store original data
    original_title = sample_schedule.title
    original_description = sample_schedule.description
    original_target_group = sample_schedule.target_group
    original_created_at = sample_schedule.created_at
    
    # Delete schedule
    response = await client.delete(
        f"/api/v1/schedules/{sample_schedule.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204
    
    # Verify data is preserved but marked as deleted
    from sqlalchemy import select
    result = await db_session.execute(
        select(Schedule).where(Schedule.id == sample_schedule.id)
    )
    deleted_schedule = result.scalar_one_or_none()
    
    assert deleted_schedule is not None
    assert deleted_schedule.deleted_at is not None
    assert deleted_schedule.title == original_title
    assert deleted_schedule.description == original_description
    assert deleted_schedule.target_group == original_target_group
    assert deleted_schedule.created_at == original_created_at


@pytest.mark.asyncio
async def test_update_deleted_schedule_fails(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    sample_schedule
):
    """Test that updating a deleted schedule fails"""
    token = create_auth_token(overall_admin)
    
    # Delete schedule
    response = await client.delete(
        f"/api/v1/schedules/{sample_schedule.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204
    
    # Try to update deleted schedule
    update_data = {
        "title": "Update Deleted Schedule"
    }
    
    response = await client.put(
        f"/api/v1/schedules/{sample_schedule.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404



# ============================================================================
# Tests for Schedule Retrieval Endpoints (Requirements 7.1, 7.5, 7.6)
# ============================================================================

@pytest.fixture
async def multiple_schedules(db_session: AsyncSession, overall_admin):
    """Create multiple schedules for different target groups"""
    schedules = []
    
    # Create schedules for Team_Members
    for i in range(3):
        schedule = Schedule(
            id=uuid.uuid4(),
            title=f"Team Schedule {i+1}",
            description=f"Team event {i+1}",
            event_date=datetime.utcnow() + timedelta(days=i+1),
            target_group=TargetGroup.TEAM_MEMBERS,
            created_by_id=overall_admin.id
        )
        db_session.add(schedule)
        schedules.append(schedule)
    
    # Create schedules for Ambassadors
    for i in range(3):
        schedule = Schedule(
            id=uuid.uuid4(),
            title=f"Ambassador Schedule {i+1}",
            description=f"Ambassador event {i+1}",
            event_date=datetime.utcnow() + timedelta(days=i+4),
            target_group=TargetGroup.AMBASSADORS,
            created_by_id=overall_admin.id
        )
        db_session.add(schedule)
        schedules.append(schedule)
    
    # Create schedules for All
    for i in range(2):
        schedule = Schedule(
            id=uuid.uuid4(),
            title=f"All Schedule {i+1}",
            description=f"Event for everyone {i+1}",
            event_date=datetime.utcnow() + timedelta(days=i+7),
            target_group=TargetGroup.ALL,
            created_by_id=overall_admin.id
        )
        db_session.add(schedule)
        schedules.append(schedule)
    
    await db_session.commit()
    for schedule in schedules:
        await db_session.refresh(schedule)
    
    return schedules


# Test Requirement 7.5: Display only group-relevant schedule events to users
# Test Property 22: Schedule Segregation
# Test Property 26: Schedule Visibility Filtering
@pytest.mark.asyncio
async def test_team_member_sees_only_team_and_all_schedules(
    client: AsyncClient,
    team_member,
    multiple_schedules
):
    """Test Team_Member sees only Team_Members and All schedules (Property 22, 26)"""
    token = create_auth_token(team_member)
    
    response = await client.get(
        "/api/v1/schedules",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Team_Member should see 3 Team_Members schedules + 2 All schedules = 5 total
    assert data["total"] == 5
    assert len(data["schedules"]) == 5
    
    # Verify all returned schedules are either Team_Members or All
    for schedule in data["schedules"]:
        assert schedule["target_group"] in ["Team_Members", "All"]
        assert schedule["target_group"] != "Ambassadors"


@pytest.mark.asyncio
async def test_ambassador_sees_only_ambassador_and_all_schedules(
    client: AsyncClient,
    ambassador,
    multiple_schedules
):
    """Test Ambassador sees only Ambassadors and All schedules (Property 22, 26)"""
    token = create_auth_token(ambassador)
    
    response = await client.get(
        "/api/v1/schedules",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Ambassador should see 3 Ambassadors schedules + 2 All schedules = 5 total
    assert data["total"] == 5
    assert len(data["schedules"]) == 5
    
    # Verify all returned schedules are either Ambassadors or All
    for schedule in data["schedules"]:
        assert schedule["target_group"] in ["Ambassadors", "All"]
        assert schedule["target_group"] != "Team_Members"


@pytest.mark.asyncio
async def test_schedule_visibility_based_on_user_type_not_role(
    client: AsyncClient,
    db_session: AsyncSession,
    multiple_schedules
):
    """Test schedule visibility is based on user_type, not role"""
    # Create an Ambassador_Admin (role=Ambassador_Admin, user_type=Ambassador)
    ambassador_admin_user = User(
        id=uuid.uuid4(),
        name="Ambassador Admin User",
        email="amb_admin_user@test.com",
        password_hash=hash_password("password123"),
        role=UserRole.AMBASSADOR_ADMIN,
        user_type=UserType.AMBASSADOR,  # user_type is Ambassador
        points=0.0
    )
    db_session.add(ambassador_admin_user)
    await db_session.commit()
    await db_session.refresh(ambassador_admin_user)
    
    token = create_auth_token(ambassador_admin_user)
    
    response = await client.get(
        "/api/v1/schedules",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Even though role is Ambassador_Admin, user_type is Ambassador
    # So should see Ambassadors and All schedules only
    assert data["total"] == 5
    for schedule in data["schedules"]:
        assert schedule["target_group"] in ["Ambassadors", "All"]


@pytest.mark.asyncio
async def test_list_schedules_pagination(
    client: AsyncClient,
    team_member,
    multiple_schedules
):
    """Test schedule list pagination works correctly"""
    token = create_auth_token(team_member)
    
    # Request page 1 with page_size=2
    response = await client.get(
        "/api/v1/schedules?page=1&page_size=2",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["schedules"]) == 2
    
    # Request page 2
    response = await client.get(
        "/api/v1/schedules?page=2&page_size=2",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 5
    assert data["page"] == 2
    assert data["page_size"] == 2
    assert len(data["schedules"]) == 2
    
    # Request page 3 (last page with 1 item)
    response = await client.get(
        "/api/v1/schedules?page=3&page_size=2",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 5
    assert data["page"] == 3
    assert len(data["schedules"]) == 1


@pytest.mark.asyncio
async def test_list_schedules_empty_result(
    client: AsyncClient,
    team_member
):
    """Test listing schedules when no schedules exist"""
    token = create_auth_token(team_member)
    
    response = await client.get(
        "/api/v1/schedules",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 0
    assert len(data["schedules"]) == 0
    assert data["page"] == 1
    assert data["page_size"] == 20


@pytest.mark.asyncio
async def test_list_schedules_excludes_deleted(
    client: AsyncClient,
    db_session: AsyncSession,
    team_member,
    multiple_schedules
):
    """Test that deleted schedules are not returned"""
    token = create_auth_token(team_member)
    
    # Get initial count
    response = await client.get(
        "/api/v1/schedules",
        headers={"Authorization": f"Bearer {token}"}
    )
    initial_count = response.json()["total"]
    
    # Soft delete one Team_Members schedule
    team_schedule = [s for s in multiple_schedules if s.target_group == TargetGroup.TEAM_MEMBERS][0]
    team_schedule.deleted_at = datetime.utcnow()
    await db_session.commit()
    
    # Get schedules again
    response = await client.get(
        "/api/v1/schedules",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have one less schedule
    assert data["total"] == initial_count - 1
    
    # Verify deleted schedule is not in results
    schedule_ids = [s["id"] for s in data["schedules"]]
    assert str(team_schedule.id) not in schedule_ids


@pytest.mark.asyncio
async def test_list_schedules_without_authentication(client: AsyncClient):
    """Test listing schedules without authentication"""
    response = await client.get("/api/v1/schedules")
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_schedules_with_invalid_token(client: AsyncClient):
    """Test listing schedules with invalid token"""
    response = await client.get(
        "/api/v1/schedules",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_schedules_invalid_page_number(
    client: AsyncClient,
    team_member
):
    """Test listing schedules with invalid page number"""
    token = create_auth_token(team_member)
    
    # Page number must be >= 1
    response = await client.get(
        "/api/v1/schedules?page=0",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_schedules_invalid_page_size(
    client: AsyncClient,
    team_member
):
    """Test listing schedules with invalid page size"""
    token = create_auth_token(team_member)
    
    # Page size must be between 1 and 100
    response = await client.get(
        "/api/v1/schedules?page_size=0",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422
    
    # Page size exceeding max
    response = await client.get(
        "/api/v1/schedules?page_size=101",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_schedules_ordered_by_event_date(
    client: AsyncClient,
    team_member,
    multiple_schedules
):
    """Test that schedules are ordered by event_date descending"""
    token = create_auth_token(team_member)
    
    response = await client.get(
        "/api/v1/schedules",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify schedules are ordered by event_date descending
    schedules = data["schedules"]
    if len(schedules) > 1:
        for i in range(len(schedules) - 1):
            current_date = datetime.fromisoformat(schedules[i]["event_date"].replace('Z', '+00:00'))
            next_date = datetime.fromisoformat(schedules[i+1]["event_date"].replace('Z', '+00:00'))
            assert current_date >= next_date


# ============================================================================
# Tests for Admin Schedule List Endpoint (Requirement 7.5)
# ============================================================================

@pytest.mark.asyncio
async def test_overall_admin_sees_all_schedules(
    client: AsyncClient,
    overall_admin,
    multiple_schedules
):
    """Test Overall_Admin can see all schedules via admin endpoint"""
    token = create_auth_token(overall_admin)
    
    response = await client.get(
        "/api/v1/schedules/admin",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should see all 8 schedules (3 Team + 3 Ambassador + 2 All)
    assert data["total"] == 8
    assert len(data["schedules"]) == 8
    
    # Verify all target groups are present
    target_groups = [s["target_group"] for s in data["schedules"]]
    assert "Team_Members" in target_groups
    assert "Ambassadors" in target_groups
    assert "All" in target_groups


@pytest.mark.asyncio
async def test_ambassador_admin_sees_all_schedules(
    client: AsyncClient,
    ambassador_admin,
    multiple_schedules
):
    """Test Ambassador_Admin can see all schedules via admin endpoint"""
    token = create_auth_token(ambassador_admin)
    
    response = await client.get(
        "/api/v1/schedules/admin",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should see all 8 schedules
    assert data["total"] == 8
    assert len(data["schedules"]) == 8


@pytest.mark.asyncio
async def test_team_member_cannot_access_admin_endpoint(
    client: AsyncClient,
    team_member,
    multiple_schedules
):
    """Test Team_Member cannot access admin schedule list (Property 27)"""
    token = create_auth_token(team_member)
    
    response = await client.get(
        "/api/v1/schedules/admin",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ambassador_cannot_access_admin_endpoint(
    client: AsyncClient,
    ambassador,
    multiple_schedules
):
    """Test Ambassador cannot access admin schedule list (Property 27)"""
    token = create_auth_token(ambassador)
    
    response = await client.get(
        "/api/v1/schedules/admin",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_endpoint_pagination(
    client: AsyncClient,
    overall_admin,
    multiple_schedules
):
    """Test admin endpoint pagination works correctly"""
    token = create_auth_token(overall_admin)
    
    # Request page 1 with page_size=3
    response = await client.get(
        "/api/v1/schedules/admin?page=1&page_size=3",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 8
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert len(data["schedules"]) == 3


@pytest.mark.asyncio
async def test_admin_endpoint_without_authentication(client: AsyncClient):
    """Test admin endpoint without authentication"""
    response = await client.get("/api/v1/schedules/admin")
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_endpoint_with_invalid_token(client: AsyncClient):
    """Test admin endpoint with invalid token"""
    response = await client.get(
        "/api/v1/schedules/admin",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


# ============================================================================
# Tests for Property 27: Non-Admin Schedule Read-Only Access
# ============================================================================

@pytest.mark.asyncio
async def test_non_admin_read_only_access_verified(
    client: AsyncClient,
    team_member,
    ambassador,
    sample_schedule
):
    """
    Test Property 27: Non-admin users have read-only access to schedules.
    
    This test verifies that:
    1. Non-admin users can read schedules (GET)
    2. Non-admin users cannot create schedules (POST) - already tested
    3. Non-admin users cannot update schedules (PUT) - already tested
    4. Non-admin users cannot delete schedules (DELETE) - already tested
    """
    # Test Team_Member can read
    team_token = create_auth_token(team_member)
    response = await client.get(
        "/api/v1/schedules",
        headers={"Authorization": f"Bearer {team_token}"}
    )
    assert response.status_code == 200
    
    # Test Ambassador can read
    amb_token = create_auth_token(ambassador)
    response = await client.get(
        "/api/v1/schedules",
        headers={"Authorization": f"Bearer {amb_token}"}
    )
    assert response.status_code == 200
    
    # Verify they cannot modify (these are already tested above, just confirming)
    # Team_Member cannot create
    response = await client.post(
        "/api/v1/schedules",
        json={
            "title": "Test",
            "description": "Test",
            "event_date": datetime.utcnow().isoformat(),
            "target_group": "Team_Members"
        },
        headers={"Authorization": f"Bearer {team_token}"}
    )
    assert response.status_code == 403
    
    # Ambassador cannot update
    response = await client.put(
        f"/api/v1/schedules/{sample_schedule.id}",
        json={"title": "Updated"},
        headers={"Authorization": f"Bearer {amb_token}"}
    )
    assert response.status_code == 403
    
    # Team_Member cannot delete
    response = await client.delete(
        f"/api/v1/schedules/{sample_schedule.id}",
        headers={"Authorization": f"Bearer {team_token}"}
    )
    assert response.status_code == 403
