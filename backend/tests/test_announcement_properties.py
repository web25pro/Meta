"""Property-based tests for announcement system

This module contains property-based tests using Hypothesis to verify
the correctness of the announcement system across a wide range of inputs.
"""
import pytest
import uuid
from datetime import datetime
from hypothesis import given, strategies as st, assume, settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserType, UserRole, Announcement
from app.models.leaderboard_schedule_announcement import TargetGroup
from app.core.security import hash_password


# Custom strategies for generating test data
@st.composite
def admin_user_strategy(draw, role=None):
    """Generate admin user data"""
    if role is None:
        role = draw(st.sampled_from([UserRole.OVERALL_ADMIN, UserRole.AMBASSADOR_ADMIN]))
    
    # Map role to appropriate user type
    if role == UserRole.OVERALL_ADMIN:
        user_type = UserType.TEAM_MEMBER
    else:
        user_type = UserType.AMBASSADOR
    
    user_data = {
        "name": f"Admin {draw(st.text(min_size=1, max_size=20))}",
        "email": f"admin_{uuid.uuid4().hex[:8]}@test.com",
        "password_hash": hash_password("password123"),
        "role": role,
        "user_type": user_type,
        "points": 0.0
    }
    
    return user_data


@st.composite
def announcement_data_strategy(draw, target_group=None):
    """Generate announcement data"""
    if target_group is None:
        target_group = draw(st.sampled_from(["Team_Members", "Ambassadors", "All"]))
    
    announcement_data = {
        "title": draw(st.text(min_size=1, max_size=255)),
        "content": draw(st.text(min_size=1, max_size=1000)),
        "target_group": target_group
    }
    
    return announcement_data


# Helper functions
async def create_test_user(db: AsyncSession, **kwargs) -> User:
    """Create a test user in the database"""
    user = User(**kwargs)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_test_announcement(db: AsyncSession, created_by_id: uuid.UUID, **kwargs) -> Announcement:
    """Create a test announcement in the database"""
    # Convert target_group string to enum if provided
    if "target_group" in kwargs and isinstance(kwargs["target_group"], str):
        kwargs["target_group"] = TargetGroup(kwargs["target_group"])
    
    announcement = Announcement(
        created_by_id=created_by_id,
        **kwargs
    )
    db.add(announcement)
    await db.commit()
    await db.refresh(announcement)
    return announcement


# Property 28: Overall Admin Announcement Targeting
@pytest.mark.asyncio
@given(
    admin_data=admin_user_strategy(role=UserRole.OVERALL_ADMIN),
    target_groups=st.lists(
        st.sampled_from(["Team_Members", "Ambassadors", "All"]),
        min_size=1,
        max_size=3,
        unique=True
    )
)
@settings(max_examples=10, deadline=None)
async def test_property_28_overall_admin_announcement_targeting(
    db_session: AsyncSession, admin_data, target_groups
):
    """
    **Validates: Requirements 8.1**
    
    Property 28: Overall Admin Announcement Targeting
    For any announcement created by an Overall_Admin, the target_group field 
    SHALL accept "Team_Members", "Ambassadors", or "All" without restriction.
    """
    # Create Overall_Admin user
    admin = await create_test_user(db_session, **admin_data)
    
    # Verify admin is Overall_Admin
    assert admin.role == UserRole.OVERALL_ADMIN, \
        f"Expected Overall_Admin, got {admin.role}"
    
    # Try creating announcements for each target group
    created_announcements = []
    
    for target_group in target_groups:
        announcement_data = {
            "title": f"Announcement for {target_group}",
            "content": f"Testing Overall_Admin can target {target_group}",
            "target_group": target_group
        }
        
        # Create announcement - should succeed for all target groups
        announcement = await create_test_announcement(
            db_session,
            created_by_id=admin.id,
            **announcement_data
        )
        
        created_announcements.append(announcement)
        
        # Verify announcement was created successfully
        assert announcement.id is not None, \
            f"Announcement for {target_group} was not created"
        
        assert announcement.target_group.value == target_group, \
            f"Expected target_group {target_group}, got {announcement.target_group.value}"
        
        assert announcement.created_by_id == admin.id, \
            f"Expected created_by_id {admin.id}, got {announcement.created_by_id}"
        
        assert announcement.title == announcement_data["title"], \
            f"Title mismatch"
        
        assert announcement.content == announcement_data["content"], \
            f"Content mismatch"
    
    # Verify all announcements were persisted
    result = await db_session.execute(
        select(Announcement).where(
            Announcement.created_by_id == admin.id,
            Announcement.deleted_at.is_(None)
        )
    )
    persisted_announcements = result.scalars().all()
    
    assert len(persisted_announcements) == len(target_groups), \
        f"Expected {len(target_groups)} announcements, found {len(persisted_announcements)}"
    
    # Verify all target groups are represented
    persisted_target_groups = {ann.target_group.value for ann in persisted_announcements}
    expected_target_groups = set(target_groups)
    
    assert persisted_target_groups == expected_target_groups, \
        f"Expected target groups {expected_target_groups}, got {persisted_target_groups}"


# Property 29: Ambassador Admin Announcement Restriction
@pytest.mark.asyncio
@given(
    admin_data=admin_user_strategy(role=UserRole.AMBASSADOR_ADMIN),
    valid_target_groups=st.lists(
        st.sampled_from(["Ambassadors", "All"]),
        min_size=1,
        max_size=2,
        unique=True
    )
)
@settings(max_examples=10, deadline=None)
async def test_property_29_ambassador_admin_announcement_restriction(
    db_session: AsyncSession, admin_data, valid_target_groups
):
    """
    **Validates: Requirements 8.2**
    
    Property 29: Ambassador Admin Announcement Restriction
    For any announcement creation attempt by an Ambassador_Admin with target_group 
    set to "Team_Members", the system SHALL reject the request with a permission error.
    
    Additionally, Ambassador_Admin SHALL be able to create announcements for 
    "Ambassadors" or "All" without restriction.
    """
    # Create Ambassador_Admin user
    admin = await create_test_user(db_session, **admin_data)
    
    # Verify admin is Ambassador_Admin
    assert admin.role == UserRole.AMBASSADOR_ADMIN, \
        f"Expected Ambassador_Admin, got {admin.role}"
    
    # Part 1: Verify Ambassador_Admin CAN create announcements for valid target groups
    created_announcements = []
    
    for target_group in valid_target_groups:
        announcement_data = {
            "title": f"Announcement for {target_group}",
            "content": f"Testing Ambassador_Admin can target {target_group}",
            "target_group": target_group
        }
        
        # Create announcement - should succeed for Ambassadors and All
        announcement = await create_test_announcement(
            db_session,
            created_by_id=admin.id,
            **announcement_data
        )
        
        created_announcements.append(announcement)
        
        # Verify announcement was created successfully
        assert announcement.id is not None, \
            f"Announcement for {target_group} was not created"
        
        assert announcement.target_group.value == target_group, \
            f"Expected target_group {target_group}, got {announcement.target_group.value}"
        
        assert announcement.created_by_id == admin.id, \
            f"Expected created_by_id {admin.id}, got {announcement.created_by_id}"
    
    # Verify valid announcements were persisted
    result = await db_session.execute(
        select(Announcement).where(
            Announcement.created_by_id == admin.id,
            Announcement.deleted_at.is_(None)
        )
    )
    persisted_announcements = result.scalars().all()
    
    assert len(persisted_announcements) == len(valid_target_groups), \
        f"Expected {len(valid_target_groups)} announcements, found {len(persisted_announcements)}"
    
    # Part 2: Verify Ambassador_Admin CANNOT create announcements for Team_Members
    # This is tested by attempting to create an announcement with target_group="Team_Members"
    # and verifying it would be rejected by the business logic
    
    # Note: Since we're testing at the model/database level, we simulate the business
    # logic check that would happen in the API endpoint. The actual rejection happens
    # in the API layer via can_create_announcement_for_group() function.
    
    # Import the RBAC function to verify the restriction
    from app.core.rbac import can_create_announcement_for_group
    
    # Verify Ambassador_Admin cannot target Team_Members
    can_target_team_members = can_create_announcement_for_group(
        admin.role,
        "Team_Members"
    )
    
    assert can_target_team_members is False, \
        "Ambassador_Admin should NOT be able to target Team_Members"
    
    # Verify Ambassador_Admin can target Ambassadors
    can_target_ambassadors = can_create_announcement_for_group(
        admin.role,
        "Ambassadors"
    )
    
    assert can_target_ambassadors is True, \
        "Ambassador_Admin should be able to target Ambassadors"
    
    # Verify Ambassador_Admin can target All
    can_target_all = can_create_announcement_for_group(
        admin.role,
        "All"
    )
    
    assert can_target_all is True, \
        "Ambassador_Admin should be able to target All"


# Additional property test: Verify announcement data persistence
@pytest.mark.asyncio
@given(
    admin_data=admin_user_strategy(),
    announcement_data=announcement_data_strategy()
)
@settings(max_examples=10, deadline=None)
async def test_announcement_data_persistence_property(
    db_session: AsyncSession, admin_data, announcement_data
):
    """
    Verify that announcement data is persisted correctly with all fields intact.
    
    This test validates that:
    - All announcement fields are stored correctly
    - Timestamps are generated automatically
    - Target group enum conversion works correctly
    """
    # Create admin user
    admin = await create_test_user(db_session, **admin_data)
    
    # Verify admin can create announcement for the target group
    from app.core.rbac import can_create_announcement_for_group
    
    can_create = can_create_announcement_for_group(
        admin.role,
        announcement_data["target_group"]
    )
    
    # Skip this test case if admin cannot create for this target group
    assume(can_create)
    
    # Create announcement
    announcement = await create_test_announcement(
        db_session,
        created_by_id=admin.id,
        **announcement_data
    )
    
    # Verify all fields are persisted correctly
    assert announcement.id is not None, "Announcement ID should be generated"
    assert announcement.title == announcement_data["title"], "Title mismatch"
    assert announcement.content == announcement_data["content"], "Content mismatch"
    assert announcement.target_group.value == announcement_data["target_group"], "Target group mismatch"
    assert announcement.created_by_id == admin.id, "Created by ID mismatch"
    assert announcement.created_at is not None, "Created at timestamp should be generated"
    assert announcement.updated_at is not None, "Updated at timestamp should be generated"
    assert announcement.deleted_at is None, "Deleted at should be None for new announcements"
    
    # Verify announcement can be retrieved from database
    result = await db_session.execute(
        select(Announcement).where(Announcement.id == announcement.id)
    )
    retrieved_announcement = result.scalar_one_or_none()
    
    assert retrieved_announcement is not None, "Announcement should be retrievable"
    assert retrieved_announcement.title == announcement_data["title"], "Retrieved title mismatch"
    assert retrieved_announcement.content == announcement_data["content"], "Retrieved content mismatch"
    assert retrieved_announcement.target_group.value == announcement_data["target_group"], "Retrieved target group mismatch"
