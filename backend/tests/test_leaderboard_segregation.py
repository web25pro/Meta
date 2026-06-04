"""Tests for leaderboard segregation enforcement (Task 9.3)

This test suite validates Requirement 6.1:
- Enforce user_type filtering in all leaderboard queries
- Prevent cross-type mixing in results
- Validate user_type values
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserType, UserRole, LeaderboardCache
from app.services.leaderboard_service import LeaderboardService


@pytest.mark.asyncio
async def test_leaderboard_cache_validates_user_type():
    """Test that LeaderboardCache validates user_type on creation"""
    import uuid
    
    # Valid user_type should work
    valid_cache = LeaderboardCache(
        user_id=uuid.uuid4(),
        user_type="Team_Member",
        rank=1,
        total_pp=100.0
    )
    assert valid_cache.user_type == "Team_Member"
    
    valid_cache2 = LeaderboardCache(
        user_id=uuid.uuid4(),
        user_type="Ambassador",
        rank=1,
        total_pp=100.0
    )
    assert valid_cache2.user_type == "Ambassador"
    
    # Invalid user_type should raise ValueError
    with pytest.raises(ValueError, match="Invalid user_type"):
        LeaderboardCache(
            user_id=uuid.uuid4(),
            user_type="InvalidType",
            rank=1,
            total_pp=100.0
        )
    
    with pytest.raises(ValueError, match="Invalid user_type"):
        LeaderboardCache(
            user_id=uuid.uuid4(),
            user_type="Admin",
            rank=1,
            total_pp=100.0
        )


@pytest.mark.asyncio
async def test_get_leaderboard_enforces_user_type_filtering(db_session: AsyncSession):
    """Test that get_leaderboard strictly filters by user_type"""
    # Create mixed users
    team_member = User(
        name="Team Member",
        email="tm@test.com",
        password_hash="hash",
        role=UserRole.TEAM_MEMBER,
        user_type=UserType.TEAM_MEMBER,
        points=100.0
    )
    ambassador = User(
        name="Ambassador",
        email="amb@test.com",
        password_hash="hash",
        role=UserRole.AMBASSADOR,
        user_type=UserType.AMBASSADOR,
        points=200.0
    )
    
    db_session.add(team_member)
    db_session.add(ambassador)
    await db_session.commit()
    
    # Refresh leaderboard cache
    await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    # Get Team_Member leaderboard
    tm_entries, tm_total = await LeaderboardService.get_leaderboard(
        db_session, UserType.TEAM_MEMBER
    )
    
    # Verify only Team_Member entries returned
    assert tm_total == 1
    assert len(tm_entries) == 1
    assert tm_entries[0].user_type == UserType.TEAM_MEMBER.value
    assert tm_entries[0].user_id == team_member.id
    
    # Get Ambassador leaderboard
    amb_entries, amb_total = await LeaderboardService.get_leaderboard(
        db_session, UserType.AMBASSADOR
    )
    
    # Verify only Ambassador entries returned
    assert amb_total == 1
    assert len(amb_entries) == 1
    assert amb_entries[0].user_type == UserType.AMBASSADOR.value
    assert amb_entries[0].user_id == ambassador.id


@pytest.mark.asyncio
async def test_leaderboard_no_cross_type_mixing(db_session: AsyncSession):
    """Test that leaderboards never mix Team_Member and Ambassador entries"""
    # Create multiple users of each type
    users = []
    
    for i in range(10):
        user = User(
            name=f"Team Member {i}",
            email=f"tm{i}@test.com",
            password_hash="hash",
            role=UserRole.TEAM_MEMBER,
            user_type=UserType.TEAM_MEMBER,
            points=float(i * 10)
        )
        db_session.add(user)
        users.append(user)
    
    for i in range(10):
        user = User(
            name=f"Ambassador {i}",
            email=f"amb{i}@test.com",
            password_hash="hash",
            role=UserRole.AMBASSADOR,
            user_type=UserType.AMBASSADOR,
            points=float(i * 20)
        )
        db_session.add(user)
        users.append(user)
    
    await db_session.commit()
    
    # Refresh leaderboard cache
    await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    # Get both leaderboards
    tm_entries, tm_total = await LeaderboardService.get_leaderboard(
        db_session, UserType.TEAM_MEMBER, page=1, page_size=100
    )
    amb_entries, amb_total = await LeaderboardService.get_leaderboard(
        db_session, UserType.AMBASSADOR, page=1, page_size=100
    )
    
    # Verify counts
    assert tm_total == 10
    assert amb_total == 10
    
    # Verify no cross-type mixing
    tm_user_ids = {entry.user_id for entry in tm_entries}
    amb_user_ids = {entry.user_id for entry in amb_entries}
    
    # No overlap between leaderboards
    assert len(tm_user_ids.intersection(amb_user_ids)) == 0
    
    # All Team_Member entries have correct user_type
    for entry in tm_entries:
        assert entry.user_type == UserType.TEAM_MEMBER.value
    
    # All Ambassador entries have correct user_type
    for entry in amb_entries:
        assert entry.user_type == UserType.AMBASSADOR.value


@pytest.mark.asyncio
async def test_get_leaderboard_validates_user_type_parameter(db_session: AsyncSession):
    """Test that get_leaderboard validates the user_type parameter"""
    # Valid UserType enum should work
    try:
        await LeaderboardService.get_leaderboard(
            db_session, UserType.TEAM_MEMBER
        )
        await LeaderboardService.get_leaderboard(
            db_session, UserType.AMBASSADOR
        )
    except ValueError:
        pytest.fail("Valid UserType enum should not raise ValueError")
    
    # Invalid type should raise ValueError
    with pytest.raises(ValueError, match="Invalid user_type"):
        await LeaderboardService.get_leaderboard(
            db_session, "InvalidType"  # type: ignore
        )


@pytest.mark.asyncio
async def test_refresh_leaderboard_maintains_segregation(db_session: AsyncSession):
    """Test that refresh_leaderboard_cache maintains type segregation"""
    # Create users with different types
    users = [
        User(
            name="TM1",
            email="tm1@test.com",
            password_hash="hash",
            role=UserRole.TEAM_MEMBER,
            user_type=UserType.TEAM_MEMBER,
            points=100.0
        ),
        User(
            name="TM2",
            email="tm2@test.com",
            password_hash="hash",
            role=UserRole.TEAM_MEMBER,
            user_type=UserType.TEAM_MEMBER,
            points=200.0
        ),
        User(
            name="AMB1",
            email="amb1@test.com",
            password_hash="hash",
            role=UserRole.AMBASSADOR,
            user_type=UserType.AMBASSADOR,
            points=150.0
        ),
        User(
            name="AMB2",
            email="amb2@test.com",
            password_hash="hash",
            role=UserRole.AMBASSADOR,
            user_type=UserType.AMBASSADOR,
            points=250.0
        ),
    ]
    
    for user in users:
        db_session.add(user)
    await db_session.commit()
    
    # Refresh cache
    result = await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    # Verify segregation in results
    assert result["team_members"] == 2
    assert result["ambassadors"] == 2
    
    # Verify rankings are independent per type
    # TM2 (200 PP) should be rank 1 among Team_Members
    tm2_rank = await LeaderboardService.get_user_rank(db_session, users[1].id)
    assert tm2_rank is not None
    assert tm2_rank.rank == 1
    assert tm2_rank.user_type == UserType.TEAM_MEMBER.value
    
    # TM1 (100 PP) should be rank 2 among Team_Members
    tm1_rank = await LeaderboardService.get_user_rank(db_session, users[0].id)
    assert tm1_rank is not None
    assert tm1_rank.rank == 2
    assert tm1_rank.user_type == UserType.TEAM_MEMBER.value
    
    # AMB2 (250 PP) should be rank 1 among Ambassadors
    amb2_rank = await LeaderboardService.get_user_rank(db_session, users[3].id)
    assert amb2_rank is not None
    assert amb2_rank.rank == 1
    assert amb2_rank.user_type == UserType.AMBASSADOR.value
    
    # AMB1 (150 PP) should be rank 2 among Ambassadors
    amb1_rank = await LeaderboardService.get_user_rank(db_session, users[2].id)
    assert amb1_rank is not None
    assert amb1_rank.rank == 2
    assert amb1_rank.user_type == UserType.AMBASSADOR.value


@pytest.mark.asyncio
async def test_leaderboard_cache_user_type_consistency(db_session: AsyncSession):
    """Test that leaderboard_cache user_type matches user's actual user_type"""
    # Create users
    team_member = User(
        name="Team Member",
        email="tm@test.com",
        password_hash="hash",
        role=UserRole.TEAM_MEMBER,
        user_type=UserType.TEAM_MEMBER,
        points=100.0
    )
    ambassador = User(
        name="Ambassador",
        email="amb@test.com",
        password_hash="hash",
        role=UserRole.AMBASSADOR,
        user_type=UserType.AMBASSADOR,
        points=200.0
    )
    
    db_session.add(team_member)
    db_session.add(ambassador)
    await db_session.commit()
    
    # Refresh cache
    await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    # Verify cache entries match user types
    tm_cache = await LeaderboardService.get_user_rank(db_session, team_member.id)
    assert tm_cache is not None
    assert tm_cache.user_type == team_member.user_type.value
    
    amb_cache = await LeaderboardService.get_user_rank(db_session, ambassador.id)
    assert amb_cache is not None
    assert amb_cache.user_type == ambassador.user_type.value


@pytest.mark.asyncio
async def test_leaderboard_pagination_maintains_segregation(db_session: AsyncSession):
    """Test that pagination doesn't break user_type segregation"""
    # Create many users of each type
    for i in range(20):
        user = User(
            name=f"Team Member {i}",
            email=f"tm{i}@test.com",
            password_hash="hash",
            role=UserRole.TEAM_MEMBER,
            user_type=UserType.TEAM_MEMBER,
            points=float(i)
        )
        db_session.add(user)
    
    for i in range(20):
        user = User(
            name=f"Ambassador {i}",
            email=f"amb{i}@test.com",
            password_hash="hash",
            role=UserRole.AMBASSADOR,
            user_type=UserType.AMBASSADOR,
            points=float(i)
        )
        db_session.add(user)
    
    await db_session.commit()
    
    # Refresh cache
    await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    # Get multiple pages of Team_Member leaderboard
    page1, total1 = await LeaderboardService.get_leaderboard(
        db_session, UserType.TEAM_MEMBER, page=1, page_size=10
    )
    page2, total2 = await LeaderboardService.get_leaderboard(
        db_session, UserType.TEAM_MEMBER, page=2, page_size=10
    )
    
    # Verify all entries are Team_Members
    for entry in page1 + page2:
        assert entry.user_type == UserType.TEAM_MEMBER.value
    
    # Get multiple pages of Ambassador leaderboard
    page1, total1 = await LeaderboardService.get_leaderboard(
        db_session, UserType.AMBASSADOR, page=1, page_size=10
    )
    page2, total2 = await LeaderboardService.get_leaderboard(
        db_session, UserType.AMBASSADOR, page=2, page_size=10
    )
    
    # Verify all entries are Ambassadors
    for entry in page1 + page2:
        assert entry.user_type == UserType.AMBASSADOR.value
