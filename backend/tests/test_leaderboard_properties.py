"""Property-based tests for leaderboard system

This module contains property-based tests using Hypothesis to verify
the correctness of the leaderboard system across a wide range of inputs.
"""
import pytest
import uuid
from datetime import datetime
from hypothesis import given, strategies as st, assume, settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserType, UserRole, LeaderboardCache
from app.services.leaderboard_service import LeaderboardService


# Custom strategies for generating test data
@st.composite
def user_list_strategy(draw, user_type=None, min_users=1, max_users=20):
    """Generate a list of users with varying point values"""
    if user_type is None:
        user_type = draw(st.sampled_from([UserType.TEAM_MEMBER, UserType.AMBASSADOR]))
    
    # Map user type to appropriate role
    if user_type == UserType.TEAM_MEMBER:
        role = UserRole.TEAM_MEMBER
    else:
        role = UserRole.AMBASSADOR
    
    num_users = draw(st.integers(min_value=min_users, max_value=max_users))
    users = []
    
    for i in range(num_users):
        user_data = {
            "name": f"User {i} {draw(st.text(min_size=1, max_size=20))}",
            "email": f"user_{uuid.uuid4().hex[:8]}_{i}@test.com",
            "password_hash": "hashed_password",
            "role": role,
            "user_type": user_type,
            "points": draw(st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False))
        }
        users.append(user_data)
    
    return users


@st.composite
def mixed_user_list_strategy(draw, min_users=2, max_users=20):
    """Generate a list of users with mixed types (Team Members and Ambassadors)"""
    num_users = draw(st.integers(min_value=min_users, max_value=max_users))
    users = []
    
    for i in range(num_users):
        user_type = draw(st.sampled_from([UserType.TEAM_MEMBER, UserType.AMBASSADOR]))
        
        # Map user type to appropriate role
        if user_type == UserType.TEAM_MEMBER:
            role = UserRole.TEAM_MEMBER
        else:
            role = UserRole.AMBASSADOR
        
        user_data = {
            "name": f"User {i} {draw(st.text(min_size=1, max_size=20))}",
            "email": f"user_{uuid.uuid4().hex[:8]}_{i}@test.com",
            "password_hash": "hashed_password",
            "role": role,
            "user_type": user_type,
            "points": draw(st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False))
        }
        users.append(user_data)
    
    return users


# Helper functions
async def create_test_user(db: AsyncSession, **kwargs) -> User:
    """Create a test user in the database"""
    user = User(**kwargs)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# Property 19: Leaderboard Segregation
@pytest.mark.asyncio
@given(users_data=mixed_user_list_strategy(min_users=4, max_users=15))
@settings(max_examples=10, deadline=None)
async def test_property_19_leaderboard_segregation(db_session: AsyncSession, users_data):
    """
    **Validates: Requirements 6.1**
    
    Property 19: Leaderboard Segregation
    For any leaderboard query, the results SHALL only include users of the 
    requested type (Team_Members or Ambassadors), with no cross-type mixing.
    """
    # Create users with mixed types
    created_users = []
    team_member_count = 0
    ambassador_count = 0
    
    for user_data in users_data:
        user = await create_test_user(db_session, **user_data)
        created_users.append(user)
        
        if user.user_type == UserType.TEAM_MEMBER:
            team_member_count += 1
        else:
            ambassador_count += 1
    
    # Ensure we have at least one of each type
    assume(team_member_count > 0 and ambassador_count > 0)
    
    # Refresh leaderboard cache
    await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    # Query Team Member leaderboard
    tm_leaderboard, tm_total = await LeaderboardService.get_leaderboard(
        db_session, UserType.TEAM_MEMBER, page=1, page_size=100
    )
    
    # Verify all entries are Team Members
    assert tm_total == team_member_count, \
        f"Expected {team_member_count} Team Members, got {tm_total}"
    
    for entry in tm_leaderboard:
        assert entry.user_type == UserType.TEAM_MEMBER.value, \
            f"Found {entry.user_type} in Team Member leaderboard"
    
    # Query Ambassador leaderboard
    amb_leaderboard, amb_total = await LeaderboardService.get_leaderboard(
        db_session, UserType.AMBASSADOR, page=1, page_size=100
    )
    
    # Verify all entries are Ambassadors
    assert amb_total == ambassador_count, \
        f"Expected {ambassador_count} Ambassadors, got {amb_total}"
    
    for entry in amb_leaderboard:
        assert entry.user_type == UserType.AMBASSADOR.value, \
            f"Found {entry.user_type} in Ambassador leaderboard"
    
    # Verify no cross-type mixing: collect all user_ids from both leaderboards
    tm_user_ids = {entry.user_id for entry in tm_leaderboard}
    amb_user_ids = {entry.user_id for entry in amb_leaderboard}
    
    # Verify no overlap
    assert len(tm_user_ids.intersection(amb_user_ids)) == 0, \
        "Found users appearing in both leaderboards"


# Property 20: Leaderboard Ranking Correctness
@pytest.mark.asyncio
@given(
    user_type=st.sampled_from([UserType.TEAM_MEMBER, UserType.AMBASSADOR]),
    users_data=st.data()
)
@settings(max_examples=10, deadline=None)
async def test_property_20_leaderboard_ranking_correctness(
    db_session: AsyncSession, user_type, users_data
):
    """
    **Validates: Requirements 6.2**
    
    Property 20: Leaderboard Ranking Correctness
    For any leaderboard of a given user type, users SHALL be ranked in descending 
    order by total_pp, with rank 1 assigned to the highest PP user, rank 2 to the 
    second highest, and so on.
    """
    # Generate users of the specified type
    users_list = users_data.draw(user_list_strategy(user_type=user_type, min_users=3, max_users=15))
    
    # Create users in database
    created_users = []
    for user_data in users_list:
        user = await create_test_user(db_session, **user_data)
        created_users.append(user)
    
    # Refresh leaderboard cache
    await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    # Get leaderboard for the user type
    leaderboard, total = await LeaderboardService.get_leaderboard(
        db_session, user_type, page=1, page_size=100
    )
    
    # Verify we got all users
    assert total == len(created_users), \
        f"Expected {len(created_users)} users, got {total}"
    
    # Verify ranking is in descending order by total_pp
    for i in range(len(leaderboard)):
        entry = leaderboard[i]
        
        # Verify rank is sequential starting from 1
        assert entry.rank == i + 1, \
            f"Expected rank {i + 1}, got {entry.rank}"
        
        # Verify descending order: each entry should have >= PP than the next
        if i < len(leaderboard) - 1:
            next_entry = leaderboard[i + 1]
            assert entry.total_pp >= next_entry.total_pp, \
                f"Rank {entry.rank} has {entry.total_pp} PP, but rank {next_entry.rank} has {next_entry.total_pp} PP (not descending)"
    
    # Verify rank 1 has the highest PP
    if len(leaderboard) > 0:
        rank_1_entry = leaderboard[0]
        assert rank_1_entry.rank == 1, "First entry should be rank 1"
        
        # Verify rank 1 has the maximum PP among all users
        max_pp = max(user.points for user in created_users)
        assert rank_1_entry.total_pp == max_pp, \
            f"Rank 1 should have {max_pp} PP, but has {rank_1_entry.total_pp} PP"
    
    # Verify the mapping between users and their ranks
    user_points_map = {user.id: float(user.points) for user in created_users}
    
    for entry in leaderboard:
        expected_pp = user_points_map[entry.user_id]
        assert entry.total_pp == expected_pp, \
            f"User {entry.user_id} should have {expected_pp} PP, but has {entry.total_pp} PP"


# Property 21: Leaderboard Position Update
@pytest.mark.asyncio
@given(
    user_type=st.sampled_from([UserType.TEAM_MEMBER, UserType.AMBASSADOR]),
    users_data=st.data(),
    point_change=st.floats(min_value=-500, max_value=500, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=10, deadline=None)
async def test_property_21_leaderboard_position_update(
    db_session: AsyncSession, user_type, users_data, point_change
):
    """
    **Validates: Requirements 6.4**
    
    Property 21: Leaderboard Position Update
    For any user whose PP balance changes, their rank in the leaderboard_cache 
    SHALL be recalculated within 10 minutes, and their new rank SHALL reflect 
    their position relative to all other users of the same type.
    
    Note: This test verifies immediate recalculation (simulating the 10-minute 
    refresh job) by calling refresh_leaderboard_cache directly.
    """
    # Generate users of the specified type
    users_list = users_data.draw(user_list_strategy(user_type=user_type, min_users=3, max_users=10))
    
    # Ensure point_change is significant enough to potentially change rank
    assume(abs(point_change) > 0.1)
    
    # Create users in database
    created_users = []
    for user_data in users_list:
        user = await create_test_user(db_session, **user_data)
        created_users.append(user)
    
    # Initial leaderboard refresh
    await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    # Select a random user to modify
    target_user = created_users[len(created_users) // 2]  # Pick middle user
    
    # Get initial rank
    initial_cache = await LeaderboardService.get_user_rank(db_session, target_user.id)
    assert initial_cache is not None, "User should have initial cache entry"
    initial_rank = initial_cache.rank
    initial_pp = initial_cache.total_pp
    
    # Modify user's points
    target_user.points = float(target_user.points) + point_change
    
    # Ensure points don't go negative
    if target_user.points < 0:
        target_user.points = 0.0
    
    await db_session.commit()
    await db_session.refresh(target_user)
    
    new_pp = float(target_user.points)
    
    # Recalculate leaderboard (simulating the background job)
    await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    # Get updated rank
    updated_cache = await LeaderboardService.get_user_rank(db_session, target_user.id)
    assert updated_cache is not None, "User should have updated cache entry"
    new_rank = updated_cache.rank
    new_cached_pp = updated_cache.total_pp
    
    # Verify the cached PP matches the user's actual PP
    assert abs(new_cached_pp - new_pp) < 0.01, \
        f"Cached PP {new_cached_pp} does not match actual PP {new_pp}"
    
    # Verify the rank reflects the new position
    # Get all users sorted by points to calculate expected rank
    all_users_sorted = sorted(
        created_users,
        key=lambda u: float(u.points),
        reverse=True
    )
    
    expected_rank = None
    for rank, user in enumerate(all_users_sorted, start=1):
        if user.id == target_user.id:
            expected_rank = rank
            break
    
    assert expected_rank is not None, "Could not find user in sorted list"
    assert new_rank == expected_rank, \
        f"Expected rank {expected_rank}, but got {new_rank}"
    
    # Verify rank changed if points changed significantly
    if abs(point_change) > 1.0:  # Significant change
        # Get the full leaderboard to verify relative positioning
        leaderboard, _ = await LeaderboardService.get_leaderboard(
            db_session, user_type, page=1, page_size=100
        )
        
        # Find the target user in the leaderboard
        target_entry = None
        for entry in leaderboard:
            if entry.user_id == target_user.id:
                target_entry = entry
                break
        
        assert target_entry is not None, "User should be in leaderboard"
        
        # Verify the user's position relative to others
        for entry in leaderboard:
            if entry.rank < target_entry.rank:
                # Users with better rank should have >= PP
                assert entry.total_pp >= target_entry.total_pp, \
                    f"Rank {entry.rank} has {entry.total_pp} PP, but rank {target_entry.rank} has {target_entry.total_pp} PP"
            elif entry.rank > target_entry.rank:
                # Users with worse rank should have <= PP
                assert entry.total_pp <= target_entry.total_pp, \
                    f"Rank {entry.rank} has {entry.total_pp} PP, but rank {target_entry.rank} has {target_entry.total_pp} PP"
