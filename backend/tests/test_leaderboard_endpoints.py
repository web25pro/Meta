"""Tests for leaderboard API endpoints"""
import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole, UserType, LeaderboardCache
from app.core.security import hash_password, create_access_token


@pytest.fixture
async def test_users(db_session: AsyncSession):
    """Create test users with different types"""
    users = []
    
    # Create Team Members
    for i in range(5):
        user = User(
            id=uuid.uuid4(),
            name=f"Team Member {i+1}",
            email=f"team{i+1}@test.com",
            password_hash=hash_password("password123"),
            role=UserRole.TEAM_MEMBER,
            user_type=UserType.TEAM_MEMBER,
            points=100.0 * (5 - i)  # Descending points
        )
        db_session.add(user)
        users.append(user)
    
    # Create Ambassadors
    for i in range(5):
        user = User(
            id=uuid.uuid4(),
            name=f"Ambassador {i+1}",
            email=f"ambassador{i+1}@test.com",
            password_hash=hash_password("password123"),
            role=UserRole.AMBASSADOR,
            user_type=UserType.AMBASSADOR,
            points=200.0 * (5 - i)  # Descending points
        )
        db_session.add(user)
        users.append(user)
    
    await db_session.commit()
    
    # Refresh to get updated data
    for user in users:
        await db_session.refresh(user)
    
    return users


@pytest.fixture
async def test_leaderboard_cache(db_session: AsyncSession, test_users):
    """Create leaderboard cache entries"""
    cache_entries = []
    
    # Team Members (first 5 users)
    for i, user in enumerate(test_users[:5]):
        cache = LeaderboardCache(
            id=uuid.uuid4(),
            user_id=user.id,
            user_type=UserType.TEAM_MEMBER.value,
            rank=i + 1,
            total_pp=user.points
        )
        db_session.add(cache)
        cache_entries.append(cache)
    
    # Ambassadors (last 5 users)
    for i, user in enumerate(test_users[5:]):
        cache = LeaderboardCache(
            id=uuid.uuid4(),
            user_id=user.id,
            user_type=UserType.AMBASSADOR.value,
            rank=i + 1,
            total_pp=user.points
        )
        db_session.add(cache)
        cache_entries.append(cache)
    
    await db_session.commit()
    
    return cache_entries


@pytest.fixture
def auth_token(test_users):
    """Create authentication token for first test user"""
    user = test_users[0]
    return create_access_token(
        user_id=str(user.id),
        role=user.role.value,
        user_type=user.user_type.value
    )


@pytest.mark.asyncio
async def test_get_team_members_leaderboard_success(
    client: AsyncClient,
    test_users,
    test_leaderboard_cache,
    auth_token
):
    """Test successful retrieval of Team_Member leaderboard"""
    response = await client.get(
        "/api/v1/leaderboard/team-members",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "entries" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    
    # Verify data
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 50
    assert len(data["entries"]) == 5
    
    # Verify entries are Team Members only
    for entry in data["entries"]:
        assert entry["user_type"] == UserType.TEAM_MEMBER.value
    
    # Verify ranking order (rank 1 should be first)
    assert data["entries"][0]["rank"] == 1
    assert data["entries"][0]["total_pp"] == 500.0


@pytest.mark.asyncio
async def test_get_ambassadors_leaderboard_success(
    client: AsyncClient,
    test_users,
    test_leaderboard_cache,
    auth_token
):
    """Test successful retrieval of Ambassador leaderboard"""
    response = await client.get(
        "/api/v1/leaderboard/ambassadors",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "entries" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    
    # Verify data
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 50
    assert len(data["entries"]) == 5
    
    # Verify entries are Ambassadors only
    for entry in data["entries"]:
        assert entry["user_type"] == UserType.AMBASSADOR.value
    
    # Verify ranking order (rank 1 should be first)
    assert data["entries"][0]["rank"] == 1
    assert data["entries"][0]["total_pp"] == 1000.0


@pytest.mark.asyncio
async def test_get_leaderboard_with_pagination(
    client: AsyncClient,
    test_users,
    test_leaderboard_cache,
    auth_token
):
    """Test leaderboard pagination"""
    # Request page 1 with page_size 2
    response = await client.get(
        "/api/v1/leaderboard/team-members?page=1&page_size=2",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["entries"]) == 2
    
    # Request page 2
    response = await client.get(
        "/api/v1/leaderboard/team-members?page=2&page_size=2",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 5
    assert data["page"] == 2
    assert data["page_size"] == 2
    assert len(data["entries"]) == 2


@pytest.mark.asyncio
async def test_get_user_rank_success(
    client: AsyncClient,
    test_users,
    test_leaderboard_cache,
    auth_token
):
    """Test successful retrieval of user rank"""
    user = test_users[0]  # First Team Member (rank 1)
    
    response = await client.get(
        f"/api/v1/leaderboard/user/{user.id}/rank",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "user_id" in data
    assert "rank" in data
    assert "total_pp" in data
    assert "user_type" in data
    
    # Verify data
    assert data["user_id"] == str(user.id)
    assert data["rank"] == 1
    assert data["total_pp"] == 500.0
    assert data["user_type"] == UserType.TEAM_MEMBER.value


@pytest.mark.asyncio
async def test_get_user_rank_not_found(
    client: AsyncClient,
    test_users,
    test_leaderboard_cache,
    auth_token
):
    """Test user rank retrieval for non-existent user"""
    non_existent_id = uuid.uuid4()
    
    response = await client.get(
        f"/api/v1/leaderboard/user/{non_existent_id}/rank",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_leaderboard_without_authentication(client: AsyncClient):
    """Test leaderboard access without authentication token"""
    response = await client.get("/api/v1/leaderboard/team-members")
    
    assert response.status_code == 403  # FastAPI HTTPBearer returns 403


@pytest.mark.asyncio
async def test_leaderboard_with_invalid_token(client: AsyncClient):
    """Test leaderboard access with invalid authentication token"""
    response = await client.get(
        "/api/v1/leaderboard/team-members",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_leaderboard_pagination_validation(
    client: AsyncClient,
    test_users,
    test_leaderboard_cache,
    auth_token
):
    """Test pagination parameter validation"""
    # Test invalid page (< 1)
    response = await client.get(
        "/api/v1/leaderboard/team-members?page=0",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 422
    
    # Test invalid page_size (> 100)
    response = await client.get(
        "/api/v1/leaderboard/team-members?page_size=101",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 422
    
    # Test invalid page_size (< 1)
    response = await client.get(
        "/api/v1/leaderboard/team-members?page_size=0",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_leaderboard_segregation(
    client: AsyncClient,
    test_users,
    test_leaderboard_cache,
    auth_token
):
    """Test that Team_Member and Ambassador leaderboards are segregated"""
    # Get Team_Member leaderboard
    tm_response = await client.get(
        "/api/v1/leaderboard/team-members",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Get Ambassador leaderboard
    amb_response = await client.get(
        "/api/v1/leaderboard/ambassadors",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert tm_response.status_code == 200
    assert amb_response.status_code == 200
    
    tm_data = tm_response.json()
    amb_data = amb_response.json()
    
    # Verify no overlap in user IDs
    tm_user_ids = {entry["user_id"] for entry in tm_data["entries"]}
    amb_user_ids = {entry["user_id"] for entry in amb_data["entries"]}
    
    assert len(tm_user_ids.intersection(amb_user_ids)) == 0
    
    # Verify all Team_Member entries have correct user_type
    for entry in tm_data["entries"]:
        assert entry["user_type"] == UserType.TEAM_MEMBER.value
    
    # Verify all Ambassador entries have correct user_type
    for entry in amb_data["entries"]:
        assert entry["user_type"] == UserType.AMBASSADOR.value
