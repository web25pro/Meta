"""Tests for announcement API endpoints"""
import pytest
import uuid
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole, UserType, Announcement
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


# ============================================================================
# Tests for Requirement 8.1: Overall_Admin can create announcements for any target_group
# Tests for Property 28: Overall Admin Announcement Targeting
# ============================================================================

@pytest.mark.asyncio
async def test_overall_admin_create_announcement_for_team_members(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """
    Test Overall_Admin can create announcement for Team_Members
    
    **Validates: Requirement 8.1**
    **Validates: Property 28 (Overall Admin Announcement Targeting)**
    """
    token = create_auth_token(overall_admin)
    
    announcement_data = {
        "title": "Team Announcement",
        "content": "Important update for all team members",
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify response structure
    assert "id" in data
    assert data["title"] == announcement_data["title"]
    assert data["content"] == announcement_data["content"]
    assert data["target_group"] == "Team_Members"
    assert data["created_by_id"] == str(overall_admin.id)
    assert "created_at" in data
    assert "updated_at" in data
    
    # Verify announcement was created in database
    from sqlalchemy import select
    result = await db_session.execute(
        select(Announcement).where(Announcement.id == uuid.UUID(data["id"]))
    )
    announcement = result.scalar_one_or_none()
    assert announcement is not None
    assert announcement.target_group == TargetGroup.TEAM_MEMBERS
    assert announcement.title == announcement_data["title"]
    assert announcement.content == announcement_data["content"]


@pytest.mark.asyncio
async def test_overall_admin_create_announcement_for_ambassadors(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """
    Test Overall_Admin can create announcement for Ambassadors
    
    **Validates: Requirement 8.1**
    **Validates: Property 28 (Overall Admin Announcement Targeting)**
    """
    token = create_auth_token(overall_admin)
    
    announcement_data = {
        "title": "Ambassador Update",
        "content": "Special announcement for ambassadors only",
        "target_group": "Ambassadors"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["target_group"] == "Ambassadors"
    assert data["created_by_id"] == str(overall_admin.id)
    
    # Verify in database
    from sqlalchemy import select
    result = await db_session.execute(
        select(Announcement).where(Announcement.id == uuid.UUID(data["id"]))
    )
    announcement = result.scalar_one_or_none()
    assert announcement is not None
    assert announcement.target_group == TargetGroup.AMBASSADORS


@pytest.mark.asyncio
async def test_overall_admin_create_announcement_for_all(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """
    Test Overall_Admin can create announcement for All
    
    **Validates: Requirement 8.1**
    **Validates: Property 28 (Overall Admin Announcement Targeting)**
    """
    token = create_auth_token(overall_admin)
    
    announcement_data = {
        "title": "Platform-Wide Announcement",
        "content": "Important update for everyone on the platform",
        "target_group": "All"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["target_group"] == "All"
    assert data["created_by_id"] == str(overall_admin.id)
    
    # Verify in database
    from sqlalchemy import select
    result = await db_session.execute(
        select(Announcement).where(Announcement.id == uuid.UUID(data["id"]))
    )
    announcement = result.scalar_one_or_none()
    assert announcement is not None
    assert announcement.target_group == TargetGroup.ALL


# ============================================================================
# Tests for Requirement 8.2: Ambassador_Admin can only create announcements for Ambassadors or All
# Tests for Property 29: Ambassador Admin Announcement Restriction
# ============================================================================

@pytest.mark.asyncio
async def test_ambassador_admin_create_announcement_for_ambassadors(
    client: AsyncClient,
    db_session: AsyncSession,
    ambassador_admin
):
    """
    Test Ambassador_Admin can create announcement for Ambassadors
    
    **Validates: Requirement 8.2**
    """
    token = create_auth_token(ambassador_admin)
    
    announcement_data = {
        "title": "Ambassador News",
        "content": "Updates for the ambassador community",
        "target_group": "Ambassadors"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["target_group"] == "Ambassadors"
    assert data["created_by_id"] == str(ambassador_admin.id)


@pytest.mark.asyncio
async def test_ambassador_admin_create_announcement_for_all(
    client: AsyncClient,
    db_session: AsyncSession,
    ambassador_admin
):
    """
    Test Ambassador_Admin can create announcement for All
    
    **Validates: Requirement 8.2**
    """
    token = create_auth_token(ambassador_admin)
    
    announcement_data = {
        "title": "General Announcement",
        "content": "Important information for everyone",
        "target_group": "All"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["target_group"] == "All"
    assert data["created_by_id"] == str(ambassador_admin.id)


@pytest.mark.asyncio
async def test_ambassador_admin_cannot_create_announcement_for_team_members(
    client: AsyncClient,
    ambassador_admin
):
    """
    Test Ambassador_Admin cannot create announcement for Team_Members
    
    **Validates: Requirement 8.2**
    **Validates: Property 29 (Ambassador Admin Announcement Restriction)**
    """
    token = create_auth_token(ambassador_admin)
    
    announcement_data = {
        "title": "Team Announcement",
        "content": "This should fail - ambassador admin cannot target team members",
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


# ============================================================================
# Tests for non-admin users cannot create announcements
# ============================================================================

@pytest.mark.asyncio
async def test_team_member_cannot_create_announcement(
    client: AsyncClient,
    team_member
):
    """Test Team_Member cannot create announcements"""
    token = create_auth_token(team_member)
    
    announcement_data = {
        "title": "Unauthorized Announcement",
        "content": "This should fail",
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ambassador_cannot_create_announcement(
    client: AsyncClient,
    ambassador
):
    """Test Ambassador cannot create announcements"""
    token = create_auth_token(ambassador)
    
    announcement_data = {
        "title": "Unauthorized Announcement",
        "content": "This should fail",
        "target_group": "Ambassadors"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


# ============================================================================
# Tests for validation (missing fields, invalid target_group, empty strings)
# ============================================================================

@pytest.mark.asyncio
async def test_create_announcement_with_invalid_target_group(
    client: AsyncClient,
    overall_admin
):
    """Test announcement creation with invalid target_group value"""
    token = create_auth_token(overall_admin)
    
    announcement_data = {
        "title": "Invalid Announcement",
        "content": "Announcement with invalid target_group",
        "target_group": "InvalidGroup"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should fail validation at schema level (422) or business logic level (400)
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_create_announcement_missing_title(
    client: AsyncClient,
    overall_admin
):
    """Test announcement creation without title"""
    token = create_auth_token(overall_admin)
    
    announcement_data = {
        "content": "Announcement without title",
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_announcement_missing_content(
    client: AsyncClient,
    overall_admin
):
    """Test announcement creation without content"""
    token = create_auth_token(overall_admin)
    
    announcement_data = {
        "title": "Announcement without content",
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_announcement_missing_target_group(
    client: AsyncClient,
    overall_admin
):
    """Test announcement creation without target_group"""
    token = create_auth_token(overall_admin)
    
    announcement_data = {
        "title": "Announcement without target_group",
        "content": "Missing target_group field"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_announcement_with_empty_title(
    client: AsyncClient,
    overall_admin
):
    """Test announcement creation with empty title"""
    token = create_auth_token(overall_admin)
    
    announcement_data = {
        "title": "",
        "content": "Testing empty title",
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_announcement_with_empty_content(
    client: AsyncClient,
    overall_admin
):
    """Test announcement creation with empty content"""
    token = create_auth_token(overall_admin)
    
    announcement_data = {
        "title": "Announcement with empty content",
        "content": "",
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_announcement_with_long_title(
    client: AsyncClient,
    overall_admin
):
    """Test announcement creation with maximum length title"""
    token = create_auth_token(overall_admin)
    
    # Title max length is 255 characters
    long_title = "A" * 255
    
    announcement_data = {
        "title": long_title,
        "content": "Testing long title",
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == long_title


@pytest.mark.asyncio
async def test_create_announcement_with_too_long_title(
    client: AsyncClient,
    overall_admin
):
    """Test announcement creation with title exceeding maximum length"""
    token = create_auth_token(overall_admin)
    
    # Title max length is 255 characters
    too_long_title = "A" * 256
    
    announcement_data = {
        "title": too_long_title,
        "content": "Testing too long title",
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


# ============================================================================
# Tests for authentication requirements
# ============================================================================

@pytest.mark.asyncio
async def test_create_announcement_without_authentication(client: AsyncClient):
    """Test announcement creation without authentication token"""
    announcement_data = {
        "title": "Unauthorized Announcement",
        "content": "Should fail without auth",
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data
    )
    
    assert response.status_code == 403  # FastAPI HTTPBearer returns 403


@pytest.mark.asyncio
async def test_create_announcement_with_invalid_token(client: AsyncClient):
    """Test announcement creation with invalid authentication token"""
    announcement_data = {
        "title": "Unauthorized Announcement",
        "content": "Should fail with invalid token",
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


# ============================================================================
# Tests for data persistence
# ============================================================================

@pytest.mark.asyncio
async def test_announcement_data_persistence(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """Test that all announcement fields are persisted correctly"""
    token = create_auth_token(overall_admin)
    
    announcement_data = {
        "title": "Persistence Test Announcement",
        "content": "Testing data persistence with special characters: @#$% and unicode: 你好 🎉",
        "target_group": "All"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Retrieve from database and verify all fields
    from sqlalchemy import select
    result = await db_session.execute(
        select(Announcement).where(Announcement.id == uuid.UUID(data["id"]))
    )
    announcement = result.scalar_one_or_none()
    
    assert announcement is not None
    assert announcement.title == announcement_data["title"]
    assert announcement.content == announcement_data["content"]
    assert announcement.target_group.value == announcement_data["target_group"]
    assert announcement.created_by_id == overall_admin.id
    assert announcement.created_at is not None
    assert announcement.updated_at is not None
    assert announcement.deleted_at is None


@pytest.mark.asyncio
async def test_announcement_timestamps(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """Test that created_at and updated_at timestamps are set correctly"""
    token = create_auth_token(overall_admin)
    
    announcement_data = {
        "title": "Timestamp Test",
        "content": "Testing timestamp generation",
        "target_group": "Team_Members"
    }
    
    before_creation = datetime.utcnow()
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    after_creation = datetime.utcnow()
    
    assert response.status_code == 201
    data = response.json()
    
    # Parse timestamps
    created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
    updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
    
    # Verify timestamps are within expected range
    assert before_creation <= created_at.replace(tzinfo=None) <= after_creation
    assert before_creation <= updated_at.replace(tzinfo=None) <= after_creation
    
    # Verify created_at and updated_at are the same for new announcements
    assert abs((created_at - updated_at).total_seconds()) < 1


# ============================================================================
# Edge cases and additional validation tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_announcement_with_long_content(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """Test announcement creation with very long content"""
    token = create_auth_token(overall_admin)
    
    # Create a long content string (10,000 characters)
    long_content = "A" * 10000
    
    announcement_data = {
        "title": "Long Content Test",
        "content": long_content,
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == long_content


@pytest.mark.asyncio
async def test_create_multiple_announcements_same_admin(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """Test that an admin can create multiple announcements"""
    token = create_auth_token(overall_admin)
    
    # Create first announcement
    announcement_data_1 = {
        "title": "First Announcement",
        "content": "First announcement content",
        "target_group": "Team_Members"
    }
    
    response_1 = await client.post(
        "/api/v1/announcements",
        json=announcement_data_1,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response_1.status_code == 201
    
    # Create second announcement
    announcement_data_2 = {
        "title": "Second Announcement",
        "content": "Second announcement content",
        "target_group": "Ambassadors"
    }
    
    response_2 = await client.post(
        "/api/v1/announcements",
        json=announcement_data_2,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response_2.status_code == 201
    
    # Verify both announcements exist and are different
    data_1 = response_1.json()
    data_2 = response_2.json()
    
    assert data_1["id"] != data_2["id"]
    assert data_1["title"] != data_2["title"]
    assert data_1["target_group"] != data_2["target_group"]


@pytest.mark.asyncio
async def test_create_announcement_with_whitespace_in_fields(
    client: AsyncClient,
    overall_admin
):
    """Test announcement creation with whitespace in title and content"""
    token = create_auth_token(overall_admin)
    
    announcement_data = {
        "title": "  Title with spaces  ",
        "content": "  Content with leading and trailing spaces  ",
        "target_group": "Team_Members"
    }
    
    response = await client.post(
        "/api/v1/announcements",
        json=announcement_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify whitespace is preserved (no automatic trimming)
    assert data["title"] == announcement_data["title"]
    assert data["content"] == announcement_data["content"]



# ============================================================================
# Tests for Requirement 8.5: Announcement update and deletion
# ============================================================================

@pytest.mark.asyncio
async def test_overall_admin_update_announcement_title(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """
    Test Overall_Admin can update announcement title
    
    **Validates: Requirement 8.5**
    """
    token = create_auth_token(overall_admin)
    
    # Create an announcement first
    announcement = Announcement(
        id=uuid.uuid4(),
        title="Original Title",
        content="Original content",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id
    )
    db_session.add(announcement)
    await db_session.commit()
    await db_session.refresh(announcement)
    
    # Update the title
    update_data = {
        "title": "Updated Title"
    }
    
    response = await client.put(
        f"/api/v1/announcements/{announcement.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["title"] == "Updated Title"
    assert data["content"] == "Original content"  # Unchanged
    assert data["target_group"] == "Team_Members"  # Unchanged
    assert data["created_at"] is not None
    assert data["updated_at"] is not None
    
    # Verify created_at is maintained
    created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
    updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
    assert updated_at >= created_at


@pytest.mark.asyncio
async def test_overall_admin_update_announcement_content(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """
    Test Overall_Admin can update announcement content
    
    **Validates: Requirement 8.5**
    """
    token = create_auth_token(overall_admin)
    
    # Create an announcement first
    announcement = Announcement(
        id=uuid.uuid4(),
        title="Test Title",
        content="Original content",
        target_group=TargetGroup.AMBASSADORS,
        created_by_id=overall_admin.id
    )
    db_session.add(announcement)
    await db_session.commit()
    await db_session.refresh(announcement)
    
    # Update the content
    update_data = {
        "content": "Updated content with new information"
    }
    
    response = await client.put(
        f"/api/v1/announcements/{announcement.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["title"] == "Test Title"  # Unchanged
    assert data["content"] == "Updated content with new information"
    assert data["target_group"] == "Ambassadors"  # Unchanged


@pytest.mark.asyncio
async def test_overall_admin_update_announcement_target_group(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """
    Test Overall_Admin can update announcement target_group
    
    **Validates: Requirement 8.5**
    """
    token = create_auth_token(overall_admin)
    
    # Create an announcement first
    announcement = Announcement(
        id=uuid.uuid4(),
        title="Test Title",
        content="Test content",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id
    )
    db_session.add(announcement)
    await db_session.commit()
    await db_session.refresh(announcement)
    
    # Update the target_group
    update_data = {
        "target_group": "Ambassadors"
    }
    
    response = await client.put(
        f"/api/v1/announcements/{announcement.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["title"] == "Test Title"  # Unchanged
    assert data["content"] == "Test content"  # Unchanged
    assert data["target_group"] == "Ambassadors"


@pytest.mark.asyncio
async def test_overall_admin_update_announcement_all_fields(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """
    Test Overall_Admin can update all announcement fields at once
    
    **Validates: Requirement 8.5**
    """
    token = create_auth_token(overall_admin)
    
    # Create an announcement first
    announcement = Announcement(
        id=uuid.uuid4(),
        title="Original Title",
        content="Original content",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id
    )
    db_session.add(announcement)
    await db_session.commit()
    await db_session.refresh(announcement)
    
    # Update all fields
    update_data = {
        "title": "Completely New Title",
        "content": "Completely new content",
        "target_group": "All"
    }
    
    response = await client.put(
        f"/api/v1/announcements/{announcement.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["title"] == "Completely New Title"
    assert data["content"] == "Completely new content"
    assert data["target_group"] == "All"


@pytest.mark.asyncio
async def test_ambassador_admin_update_announcement_for_ambassadors(
    client: AsyncClient,
    db_session: AsyncSession,
    ambassador_admin
):
    """
    Test Ambassador_Admin can update announcement for Ambassadors
    
    **Validates: Requirement 8.5**
    """
    token = create_auth_token(ambassador_admin)
    
    # Create an announcement first
    announcement = Announcement(
        id=uuid.uuid4(),
        title="Ambassador Announcement",
        content="Original content",
        target_group=TargetGroup.AMBASSADORS,
        created_by_id=ambassador_admin.id
    )
    db_session.add(announcement)
    await db_session.commit()
    await db_session.refresh(announcement)
    
    # Update the announcement
    update_data = {
        "title": "Updated Ambassador Announcement"
    }
    
    response = await client.put(
        f"/api/v1/announcements/{announcement.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["title"] == "Updated Ambassador Announcement"


@pytest.mark.asyncio
async def test_ambassador_admin_cannot_update_to_team_members(
    client: AsyncClient,
    db_session: AsyncSession,
    ambassador_admin
):
    """
    Test Ambassador_Admin cannot update announcement to Team_Members target_group
    
    **Validates: Requirement 8.5**
    """
    token = create_auth_token(ambassador_admin)
    
    # Create an announcement first
    announcement = Announcement(
        id=uuid.uuid4(),
        title="Ambassador Announcement",
        content="Original content",
        target_group=TargetGroup.AMBASSADORS,
        created_by_id=ambassador_admin.id
    )
    db_session.add(announcement)
    await db_session.commit()
    await db_session.refresh(announcement)
    
    # Try to update to Team_Members
    update_data = {
        "target_group": "Team_Members"
    }
    
    response = await client.put(
        f"/api/v1/announcements/{announcement.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_team_member_cannot_update_announcement(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    team_member
):
    """
    Test Team_Member cannot update announcements
    
    **Validates: Requirement 8.5**
    """
    # Create an announcement as admin
    announcement = Announcement(
        id=uuid.uuid4(),
        title="Test Announcement",
        content="Test content",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id
    )
    db_session.add(announcement)
    await db_session.commit()
    await db_session.refresh(announcement)
    
    # Try to update as team member
    token = create_auth_token(team_member)
    update_data = {
        "title": "Unauthorized Update"
    }
    
    response = await client.put(
        f"/api/v1/announcements/{announcement.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_nonexistent_announcement(
    client: AsyncClient,
    overall_admin
):
    """
    Test updating a non-existent announcement returns 404
    
    **Validates: Requirement 8.5**
    """
    token = create_auth_token(overall_admin)
    
    fake_id = uuid.uuid4()
    update_data = {
        "title": "Updated Title"
    }
    
    response = await client.put(
        f"/api/v1/announcements/{fake_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_announcement_with_invalid_target_group(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """
    Test updating announcement with invalid target_group value
    
    **Validates: Requirement 8.5**
    """
    token = create_auth_token(overall_admin)
    
    # Create an announcement first
    announcement = Announcement(
        id=uuid.uuid4(),
        title="Test Announcement",
        content="Test content",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id
    )
    db_session.add(announcement)
    await db_session.commit()
    await db_session.refresh(announcement)
    
    # Try to update with invalid target_group
    update_data = {
        "target_group": "InvalidGroup"
    }
    
    response = await client.put(
        f"/api/v1/announcements/{announcement.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_overall_admin_delete_announcement(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """
    Test Overall_Admin can delete announcement (soft delete)
    
    **Validates: Requirement 8.5**
    """
    token = create_auth_token(overall_admin)
    
    # Create an announcement first
    announcement = Announcement(
        id=uuid.uuid4(),
        title="Announcement to Delete",
        content="This will be deleted",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id
    )
    db_session.add(announcement)
    await db_session.commit()
    await db_session.refresh(announcement)
    
    # Delete the announcement
    response = await client.delete(
        f"/api/v1/announcements/{announcement.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204
    
    # Verify soft delete - announcement should have deleted_at set
    from sqlalchemy import select
    result = await db_session.execute(
        select(Announcement).where(Announcement.id == announcement.id)
    )
    deleted_announcement = result.scalar_one_or_none()
    
    assert deleted_announcement is not None
    assert deleted_announcement.deleted_at is not None


@pytest.mark.asyncio
async def test_ambassador_admin_delete_announcement_for_ambassadors(
    client: AsyncClient,
    db_session: AsyncSession,
    ambassador_admin
):
    """
    Test Ambassador_Admin can delete announcement for Ambassadors
    
    **Validates: Requirement 8.5**
    """
    token = create_auth_token(ambassador_admin)
    
    # Create an announcement first
    announcement = Announcement(
        id=uuid.uuid4(),
        title="Ambassador Announcement",
        content="To be deleted",
        target_group=TargetGroup.AMBASSADORS,
        created_by_id=ambassador_admin.id
    )
    db_session.add(announcement)
    await db_session.commit()
    await db_session.refresh(announcement)
    
    # Delete the announcement
    response = await client.delete(
        f"/api/v1/announcements/{announcement.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_ambassador_admin_cannot_delete_team_members_announcement(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    ambassador_admin
):
    """
    Test Ambassador_Admin cannot delete announcement for Team_Members
    
    **Validates: Requirement 8.5**
    """
    # Create a Team_Members announcement as Overall_Admin
    announcement = Announcement(
        id=uuid.uuid4(),
        title="Team Members Announcement",
        content="For team members only",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id
    )
    db_session.add(announcement)
    await db_session.commit()
    await db_session.refresh(announcement)
    
    # Try to delete as Ambassador_Admin
    token = create_auth_token(ambassador_admin)
    
    response = await client.delete(
        f"/api/v1/announcements/{announcement.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_team_member_cannot_delete_announcement(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    team_member
):
    """
    Test Team_Member cannot delete announcements
    
    **Validates: Requirement 8.5**
    """
    # Create an announcement as admin
    announcement = Announcement(
        id=uuid.uuid4(),
        title="Test Announcement",
        content="Test content",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id
    )
    db_session.add(announcement)
    await db_session.commit()
    await db_session.refresh(announcement)
    
    # Try to delete as team member
    token = create_auth_token(team_member)
    
    response = await client.delete(
        f"/api/v1/announcements/{announcement.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_nonexistent_announcement(
    client: AsyncClient,
    overall_admin
):
    """
    Test deleting a non-existent announcement returns 404
    
    **Validates: Requirement 8.5**
    """
    token = create_auth_token(overall_admin)
    
    fake_id = uuid.uuid4()
    
    response = await client.delete(
        f"/api/v1/announcements/{fake_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_already_deleted_announcement(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """
    Test deleting an already deleted announcement returns 404
    
    **Validates: Requirement 8.5**
    """
    token = create_auth_token(overall_admin)
    
    # Create and soft delete an announcement
    announcement = Announcement(
        id=uuid.uuid4(),
        title="Already Deleted",
        content="This is already deleted",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id,
        deleted_at=datetime.utcnow()
    )
    db_session.add(announcement)
    await db_session.commit()
    await db_session.refresh(announcement)
    
    # Try to delete again
    response = await client.delete(
        f"/api/v1/announcements/{announcement.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_maintains_created_at_timestamp(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """
    Test that updating an announcement maintains the original created_at timestamp
    
    **Validates: Requirement 8.5**
    """
    token = create_auth_token(overall_admin)
    
    # Create an announcement
    announcement = Announcement(
        id=uuid.uuid4(),
        title="Original Title",
        content="Original content",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id
    )
    db_session.add(announcement)
    await db_session.commit()
    await db_session.refresh(announcement)
    
    original_created_at = announcement.created_at
    
    # Wait a moment to ensure timestamps would differ
    import asyncio
    await asyncio.sleep(0.1)
    
    # Update the announcement
    update_data = {
        "title": "Updated Title"
    }
    
    response = await client.put(
        f"/api/v1/announcements/{announcement.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify created_at is unchanged
    updated_created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
    assert abs((updated_created_at.replace(tzinfo=None) - original_created_at).total_seconds()) < 1
    
    # Verify updated_at is different
    updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
    assert updated_at.replace(tzinfo=None) > original_created_at



# ============================================================================
# Tests for Requirement 8.3, 8.4: Announcement retrieval with visibility filtering
# Tests for Property 30: Announcement Visibility Filtering
# Tests for Property 31: Announcement Chronological Ordering
# ============================================================================

@pytest.mark.asyncio
async def test_team_member_sees_team_members_and_all_announcements(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    team_member
):
    """
    Test Team_Member sees announcements with target_group = Team_Members or All
    
    **Validates: Requirements 8.3, 8.4**
    **Validates: Property 30 (Announcement Visibility Filtering)**
    """
    # Create announcements with different target groups
    announcement_team = Announcement(
        id=uuid.uuid4(),
        title="Team Announcement",
        content="For team members",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id
    )
    announcement_ambassador = Announcement(
        id=uuid.uuid4(),
        title="Ambassador Announcement",
        content="For ambassadors",
        target_group=TargetGroup.AMBASSADORS,
        created_by_id=overall_admin.id
    )
    announcement_all = Announcement(
        id=uuid.uuid4(),
        title="All Announcement",
        content="For everyone",
        target_group=TargetGroup.ALL,
        created_by_id=overall_admin.id
    )
    
    db_session.add_all([announcement_team, announcement_ambassador, announcement_all])
    await db_session.commit()
    
    # Query as team member
    token = create_auth_token(team_member)
    response = await client.get(
        "/api/v1/announcements",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should see Team_Members and All announcements, but not Ambassadors
    assert data["total"] == 2
    assert len(data["announcements"]) == 2
    
    announcement_ids = [a["id"] for a in data["announcements"]]
    assert str(announcement_team.id) in announcement_ids
    assert str(announcement_all.id) in announcement_ids
    assert str(announcement_ambassador.id) not in announcement_ids


@pytest.mark.asyncio
async def test_ambassador_sees_ambassadors_and_all_announcements(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    ambassador
):
    """
    Test Ambassador sees announcements with target_group = Ambassadors or All
    
    **Validates: Requirements 8.3, 8.4**
    **Validates: Property 30 (Announcement Visibility Filtering)**
    """
    # Create announcements with different target groups
    announcement_team = Announcement(
        id=uuid.uuid4(),
        title="Team Announcement",
        content="For team members",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id
    )
    announcement_ambassador = Announcement(
        id=uuid.uuid4(),
        title="Ambassador Announcement",
        content="For ambassadors",
        target_group=TargetGroup.AMBASSADORS,
        created_by_id=overall_admin.id
    )
    announcement_all = Announcement(
        id=uuid.uuid4(),
        title="All Announcement",
        content="For everyone",
        target_group=TargetGroup.ALL,
        created_by_id=overall_admin.id
    )
    
    db_session.add_all([announcement_team, announcement_ambassador, announcement_all])
    await db_session.commit()
    
    # Query as ambassador
    token = create_auth_token(ambassador)
    response = await client.get(
        "/api/v1/announcements",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should see Ambassadors and All announcements, but not Team_Members
    assert data["total"] == 2
    assert len(data["announcements"]) == 2
    
    announcement_ids = [a["id"] for a in data["announcements"]]
    assert str(announcement_ambassador.id) in announcement_ids
    assert str(announcement_all.id) in announcement_ids
    assert str(announcement_team.id) not in announcement_ids


@pytest.mark.asyncio
async def test_announcements_ordered_by_created_at_descending(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    team_member
):
    """
    Test announcements are ordered by created_at descending (newest first)
    
    **Validates: Requirement 8.4**
    **Validates: Property 31 (Announcement Chronological Ordering)**
    """
    import asyncio
    
    # Create announcements with different timestamps
    announcement_1 = Announcement(
        id=uuid.uuid4(),
        title="First Announcement",
        content="Created first",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id,
        created_at=datetime(2024, 1, 1, 10, 0, 0)
    )
    db_session.add(announcement_1)
    await db_session.commit()
    
    await asyncio.sleep(0.01)
    
    announcement_2 = Announcement(
        id=uuid.uuid4(),
        title="Second Announcement",
        content="Created second",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id,
        created_at=datetime(2024, 1, 2, 10, 0, 0)
    )
    db_session.add(announcement_2)
    await db_session.commit()
    
    await asyncio.sleep(0.01)
    
    announcement_3 = Announcement(
        id=uuid.uuid4(),
        title="Third Announcement",
        content="Created third (newest)",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id,
        created_at=datetime(2024, 1, 3, 10, 0, 0)
    )
    db_session.add(announcement_3)
    await db_session.commit()
    
    # Query as team member
    token = create_auth_token(team_member)
    response = await client.get(
        "/api/v1/announcements",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["announcements"]) == 3
    
    # Verify order: newest first (announcement_3, announcement_2, announcement_1)
    assert data["announcements"][0]["id"] == str(announcement_3.id)
    assert data["announcements"][1]["id"] == str(announcement_2.id)
    assert data["announcements"][2]["id"] == str(announcement_1.id)
    
    # Verify timestamps are in descending order
    timestamps = [
        datetime.fromisoformat(a["created_at"].replace('Z', '+00:00'))
        for a in data["announcements"]
    ]
    assert timestamps[0] > timestamps[1] > timestamps[2]


@pytest.mark.asyncio
async def test_announcements_exclude_deleted(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    team_member
):
    """
    Test that deleted announcements are excluded from results
    
    **Validates: Requirements 8.3, 8.4**
    """
    # Create active announcement
    announcement_active = Announcement(
        id=uuid.uuid4(),
        title="Active Announcement",
        content="This is active",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id
    )
    
    # Create deleted announcement
    announcement_deleted = Announcement(
        id=uuid.uuid4(),
        title="Deleted Announcement",
        content="This is deleted",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id,
        deleted_at=datetime.utcnow()
    )
    
    db_session.add_all([announcement_active, announcement_deleted])
    await db_session.commit()
    
    # Query as team member
    token = create_auth_token(team_member)
    response = await client.get(
        "/api/v1/announcements",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only see active announcement
    assert data["total"] == 1
    assert len(data["announcements"]) == 1
    assert data["announcements"][0]["id"] == str(announcement_active.id)


@pytest.mark.asyncio
async def test_announcements_pagination(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    team_member
):
    """
    Test announcement list pagination
    
    **Validates: Requirements 8.3, 8.4**
    """
    # Create 25 announcements
    announcements = []
    for i in range(25):
        announcement = Announcement(
            id=uuid.uuid4(),
            title=f"Announcement {i}",
            content=f"Content {i}",
            target_group=TargetGroup.TEAM_MEMBERS,
            created_by_id=overall_admin.id,
            created_at=datetime(2024, 1, 1, 10, i, 0)
        )
        announcements.append(announcement)
    
    db_session.add_all(announcements)
    await db_session.commit()
    
    token = create_auth_token(team_member)
    
    # Get first page (default page_size=20)
    response = await client.get(
        "/api/v1/announcements?page=1&page_size=20",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 25
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert len(data["announcements"]) == 20
    
    # Get second page
    response = await client.get(
        "/api/v1/announcements?page=2&page_size=20",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 25
    assert data["page"] == 2
    assert data["page_size"] == 20
    assert len(data["announcements"]) == 5


@pytest.mark.asyncio
async def test_announcements_pagination_custom_page_size(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin,
    team_member
):
    """
    Test announcement list pagination with custom page size
    
    **Validates: Requirements 8.3, 8.4**
    """
    # Create 15 announcements
    announcements = []
    for i in range(15):
        announcement = Announcement(
            id=uuid.uuid4(),
            title=f"Announcement {i}",
            content=f"Content {i}",
            target_group=TargetGroup.TEAM_MEMBERS,
            created_by_id=overall_admin.id
        )
        announcements.append(announcement)
    
    db_session.add_all(announcements)
    await db_session.commit()
    
    token = create_auth_token(team_member)
    
    # Get with page_size=5
    response = await client.get(
        "/api/v1/announcements?page=1&page_size=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 15
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert len(data["announcements"]) == 5


@pytest.mark.asyncio
async def test_announcements_without_authentication(
    client: AsyncClient
):
    """
    Test announcement list requires authentication
    
    **Validates: Requirements 8.3, 8.4**
    """
    response = await client.get("/api/v1/announcements")
    
    assert response.status_code == 403  # FastAPI HTTPBearer returns 403


@pytest.mark.asyncio
async def test_announcements_with_invalid_token(
    client: AsyncClient
):
    """
    Test announcement list with invalid authentication token
    
    **Validates: Requirements 8.3, 8.4**
    """
    response = await client.get(
        "/api/v1/announcements",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_list_all_announcements(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """
    Test admin endpoint returns all announcements regardless of target_group
    
    **Validates: Requirements 8.1, 8.2**
    """
    # Create announcements with different target groups
    announcement_team = Announcement(
        id=uuid.uuid4(),
        title="Team Announcement",
        content="For team members",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id
    )
    announcement_ambassador = Announcement(
        id=uuid.uuid4(),
        title="Ambassador Announcement",
        content="For ambassadors",
        target_group=TargetGroup.AMBASSADORS,
        created_by_id=overall_admin.id
    )
    announcement_all = Announcement(
        id=uuid.uuid4(),
        title="All Announcement",
        content="For everyone",
        target_group=TargetGroup.ALL,
        created_by_id=overall_admin.id
    )
    
    db_session.add_all([announcement_team, announcement_ambassador, announcement_all])
    await db_session.commit()
    
    # Query as admin
    token = create_auth_token(overall_admin)
    response = await client.get(
        "/api/v1/announcements/admin",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should see all announcements
    assert data["total"] == 3
    assert len(data["announcements"]) == 3
    
    announcement_ids = [a["id"] for a in data["announcements"]]
    assert str(announcement_team.id) in announcement_ids
    assert str(announcement_ambassador.id) in announcement_ids
    assert str(announcement_all.id) in announcement_ids


@pytest.mark.asyncio
async def test_ambassador_admin_can_access_admin_list(
    client: AsyncClient,
    db_session: AsyncSession,
    ambassador_admin
):
    """
    Test Ambassador_Admin can access admin announcement list
    
    **Validates: Requirements 8.1, 8.2**
    """
    # Create an announcement
    announcement = Announcement(
        id=uuid.uuid4(),
        title="Test Announcement",
        content="Test content",
        target_group=TargetGroup.AMBASSADORS,
        created_by_id=ambassador_admin.id
    )
    db_session.add(announcement)
    await db_session.commit()
    
    # Query as ambassador admin
    token = create_auth_token(ambassador_admin)
    response = await client.get(
        "/api/v1/announcements/admin",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_team_member_cannot_access_admin_list(
    client: AsyncClient,
    team_member
):
    """
    Test Team_Member cannot access admin announcement list
    
    **Validates: Requirements 8.1, 8.2**
    """
    token = create_auth_token(team_member)
    response = await client.get(
        "/api/v1/announcements/admin",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ambassador_cannot_access_admin_list(
    client: AsyncClient,
    ambassador
):
    """
    Test Ambassador cannot access admin announcement list
    
    **Validates: Requirements 8.1, 8.2**
    """
    token = create_auth_token(ambassador)
    response = await client.get(
        "/api/v1/announcements/admin",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_list_ordered_by_created_at_descending(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """
    Test admin announcement list is ordered by created_at descending
    
    **Validates: Requirements 8.1, 8.2, 8.4**
    """
    import asyncio
    
    # Create announcements with different timestamps
    announcement_1 = Announcement(
        id=uuid.uuid4(),
        title="First Announcement",
        content="Created first",
        target_group=TargetGroup.TEAM_MEMBERS,
        created_by_id=overall_admin.id,
        created_at=datetime(2024, 1, 1, 10, 0, 0)
    )
    db_session.add(announcement_1)
    await db_session.commit()
    
    await asyncio.sleep(0.01)
    
    announcement_2 = Announcement(
        id=uuid.uuid4(),
        title="Second Announcement",
        content="Created second (newest)",
        target_group=TargetGroup.AMBASSADORS,
        created_by_id=overall_admin.id,
        created_at=datetime(2024, 1, 2, 10, 0, 0)
    )
    db_session.add(announcement_2)
    await db_session.commit()
    
    # Query as admin
    token = create_auth_token(overall_admin)
    response = await client.get(
        "/api/v1/announcements/admin",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["announcements"]) >= 2
    
    # Verify newest is first
    assert data["announcements"][0]["id"] == str(announcement_2.id)
    assert data["announcements"][1]["id"] == str(announcement_1.id)


@pytest.mark.asyncio
async def test_admin_list_pagination(
    client: AsyncClient,
    db_session: AsyncSession,
    overall_admin
):
    """
    Test admin announcement list pagination
    
    **Validates: Requirements 8.1, 8.2**
    """
    # Create 25 announcements
    announcements = []
    for i in range(25):
        announcement = Announcement(
            id=uuid.uuid4(),
            title=f"Announcement {i}",
            content=f"Content {i}",
            target_group=TargetGroup.ALL,
            created_by_id=overall_admin.id
        )
        announcements.append(announcement)
    
    db_session.add_all(announcements)
    await db_session.commit()
    
    token = create_auth_token(overall_admin)
    
    # Get first page
    response = await client.get(
        "/api/v1/announcements/admin?page=1&page_size=20",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] >= 25
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert len(data["announcements"]) == 20
