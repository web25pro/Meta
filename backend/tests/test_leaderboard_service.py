"""Tests for leaderboard service"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserType, UserRole, LeaderboardCache
from app.services.leaderboard_service import LeaderboardService


@pytest.mark.asyncio
async def test_refresh_leaderboard_cache_empty(db_session: AsyncSession):
    """Test leaderboard refresh with no users"""
    result = await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    assert result["status"] == "completed"
    assert result["users_updated"] == 0


@pytest.mark.asyncio
async def test_refresh_leaderboard_cache_with_users(db_session: AsyncSession):
    """Test leaderboard refresh with multiple users"""
    # Create test users with different points
    users = [
        User(
            name="Team Member 1",
            email="tm1@example.com",
            password_hash="hash",
            role=UserRole.TEAM_MEMBER,
            user_type=UserType.TEAM_MEMBER,
            points=100.0
        ),
        User(
            name="Team Member 2",
            email="tm2@example.com",
            password_hash="hash",
            role=UserRole.TEAM_MEMBER,
            user_type=UserType.TEAM_MEMBER,
            points=200.0
        ),
        User(
            name="Ambassador 1",
            email="amb1@example.com",
            password_hash="hash",
            role=UserRole.AMBASSADOR,
            user_type=UserType.AMBASSADOR,
            points=150.0
        ),
        User(
            name="Ambassador 2",
            email="amb2@example.com",
            password_hash="hash",
            role=UserRole.AMBASSADOR,
            user_type=UserType.AMBASSADOR,
            points=250.0
        ),
    ]
    
    for user in users:
        db_session.add(user)
    await db_session.commit()
    
    # Refresh leaderboard cache
    result = await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    assert result["status"] == "completed"
    assert result["users_updated"] == 4
    assert result["team_members"] == 2
    assert result["ambassadors"] == 2
    
    # Verify rankings are correct
    # Team Member 2 (200 PP) should be rank 1
    tm2_cache = await LeaderboardService.get_user_rank(db_session, users[1].id)
    assert tm2_cache is not None
    assert tm2_cache.rank == 1
    assert tm2_cache.total_pp == 200.0
    
    # Team Member 1 (100 PP) should be rank 2
    tm1_cache = await LeaderboardService.get_user_rank(db_session, users[0].id)
    assert tm1_cache is not None
    assert tm1_cache.rank == 2
    assert tm1_cache.total_pp == 100.0
    
    # Ambassador 2 (250 PP) should be rank 1
    amb2_cache = await LeaderboardService.get_user_rank(db_session, users[3].id)
    assert amb2_cache is not None
    assert amb2_cache.rank == 1
    assert amb2_cache.total_pp == 250.0
    
    # Ambassador 1 (150 PP) should be rank 2
    amb1_cache = await LeaderboardService.get_user_rank(db_session, users[2].id)
    assert amb1_cache is not None
    assert amb1_cache.rank == 2
    assert amb1_cache.total_pp == 150.0


@pytest.mark.asyncio
async def test_get_leaderboard_by_type(db_session: AsyncSession):
    """Test getting leaderboard filtered by user type"""
    # Create test users
    users = [
        User(
            name="Team Member 1",
            email="tm1@example.com",
            password_hash="hash",
            role=UserRole.TEAM_MEMBER,
            user_type=UserType.TEAM_MEMBER,
            points=100.0
        ),
        User(
            name="Ambassador 1",
            email="amb1@example.com",
            password_hash="hash",
            role=UserRole.AMBASSADOR,
            user_type=UserType.AMBASSADOR,
            points=150.0
        ),
    ]
    
    for user in users:
        db_session.add(user)
    await db_session.commit()
    
    # Refresh cache
    await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    # Get Team Member leaderboard
    tm_leaderboard, tm_total = await LeaderboardService.get_leaderboard(
        db_session, UserType.TEAM_MEMBER
    )
    assert tm_total == 1
    assert len(tm_leaderboard) == 1
    assert tm_leaderboard[0].user_type == UserType.TEAM_MEMBER.value
    
    # Get Ambassador leaderboard
    amb_leaderboard, amb_total = await LeaderboardService.get_leaderboard(
        db_session, UserType.AMBASSADOR
    )
    assert amb_total == 1
    assert len(amb_leaderboard) == 1
    assert amb_leaderboard[0].user_type == UserType.AMBASSADOR.value


@pytest.mark.asyncio
async def test_leaderboard_ranking_order(db_session: AsyncSession):
    """Test that leaderboard ranks users in descending order by total_pp"""
    # Create users with specific point values
    users = [
        User(
            name=f"User {i}",
            email=f"user{i}@example.com",
            password_hash="hash",
            role=UserRole.TEAM_MEMBER,
            user_type=UserType.TEAM_MEMBER,
            points=float(i * 10)
        )
        for i in range(1, 6)  # 10, 20, 30, 40, 50 points
    ]
    
    for user in users:
        db_session.add(user)
    await db_session.commit()
    
    # Refresh cache
    await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    # Get leaderboard
    leaderboard, total = await LeaderboardService.get_leaderboard(
        db_session, UserType.TEAM_MEMBER
    )
    
    assert total == 5
    assert len(leaderboard) == 5
    
    # Verify descending order
    for i, entry in enumerate(leaderboard):
        assert entry.rank == i + 1
        # Highest points should be rank 1
        expected_points = float((5 - i) * 10)
        assert entry.total_pp == expected_points
