"""
Test suite for Task 19 Checkpoint: Background Jobs and Real-Time Complete

This test suite verifies:
1. Deadline enforcement job runs successfully
2. Leaderboard cache updates correctly
3. Background job integration
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import (
    User, Task, TaskAssignment, TaskSubmission, DeadlinePenaltyApplied,
    LeaderboardCache, PointsTransaction, TransactionType, UserType, UserRole, AssignedGroup
)
from app.tasks.deadline_enforcement import _check_deadline_penalties_async
from app.services.leaderboard_service import LeaderboardService
from app.services.points_service import PointsService


@pytest.mark.asyncio
async def test_deadline_enforcement_no_overdue_tasks(db_session: AsyncSession):
    """Test deadline enforcement with no overdue tasks"""
    result = await _check_deadline_penalties_async()
    
    assert result["status"] == "completed"
    assert result["penalties_applied"] == 0
    assert result["tasks_checked"] == 0


@pytest.mark.asyncio
async def test_deadline_enforcement_with_submission(db_session: AsyncSession):
    """Test that deadline enforcement does not penalize users who submitted"""
    # Create user
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User",
        role=UserRole.TEAM_MEMBER,
        user_type=UserType.TEAM_MEMBER,
        points=100.0
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create overdue task
    task = Task(
        title="Overdue Task",
        description="Test task",
        assigned_to_group=AssignedGroup.TEAM_MEMBERS,
        deadline=datetime.utcnow() - timedelta(hours=1),
        point_value=50.0,
        created_by_id=user.id
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    # Create assignment
    assignment = TaskAssignment(task_id=task.id, user_id=user.id)
    db_session.add(assignment)
    
    # Create submission
    submission = TaskSubmission(
        task_id=task.id,
        user_id=user.id,
        submission_text="Test submission"
    )
    db_session.add(submission)
    await db_session.commit()
    
    # Run deadline enforcement
    result = await _check_deadline_penalties_async()
    
    # Verify no penalty was applied
    assert result["status"] == "completed"
    assert result["penalties_applied"] == 0
    assert result["tasks_checked"] == 1
    
    # Verify user points unchanged
    await db_session.refresh(user)
    assert float(user.points) == 100.0


@pytest.mark.asyncio
async def test_deadline_enforcement_applies_penalty(db_session: AsyncSession):
    """Test that deadline enforcement applies penalty for missed deadline"""
    # Create user with sufficient points
    user = User(
        email="test2@example.com",
        hashed_password="hashed",
        full_name="Test User 2",
        role=UserRole.TEAM_MEMBER,
        user_type=UserType.TEAM_MEMBER,
        points=200.0
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create overdue task
    task = Task(
        title="Overdue Task 2",
        description="Test task",
        assigned_to_group=AssignedGroup.TEAM_MEMBERS,
        deadline=datetime.utcnow() - timedelta(hours=2),
        point_value=50.0,
        created_by_id=user.id
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    # Create assignment (no submission)
    assignment = TaskAssignment(task_id=task.id, user_id=user.id)
    db_session.add(assignment)
    await db_session.commit()
    
    # Run deadline enforcement
    result = await _check_deadline_penalties_async()
    
    # Verify penalty was applied
    assert result["status"] == "completed"
    assert result["penalties_applied"] == 1
    assert result["tasks_checked"] == 1
    
    # Verify penalty record was created
    penalty_result = await db_session.execute(
        select(DeadlinePenaltyApplied).where(
            DeadlinePenaltyApplied.task_id == task.id,
            DeadlinePenaltyApplied.user_id == user.id
        )
    )
    penalty_record = penalty_result.scalar_one_or_none()
    assert penalty_record is not None
    
    # Verify points transaction was created
    transaction_result = await db_session.execute(
        select(PointsTransaction).where(
            PointsTransaction.user_id == user.id,
            PointsTransaction.transaction_type == TransactionType.DEADLINE_PENALTY,
            PointsTransaction.related_task_id == task.id
        )
    )
    transaction = transaction_result.scalar_one_or_none()
    assert transaction is not None
    assert float(transaction.amount) == -100.0
    
    # Verify user points were deducted
    await db_session.refresh(user)
    assert float(user.points) == 100.0


@pytest.mark.asyncio
async def test_deadline_enforcement_idempotency(db_session: AsyncSession):
    """Test that deadline enforcement does not apply penalty twice"""
    # Create user
    user = User(
        email="test3@example.com",
        hashed_password="hashed",
        full_name="Test User 3",
        role=UserRole.TEAM_MEMBER,
        user_type=UserType.TEAM_MEMBER,
        points=300.0
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create overdue task
    task = Task(
        title="Overdue Task 3",
        description="Test task",
        assigned_to_group=AssignedGroup.TEAM_MEMBERS,
        deadline=datetime.utcnow() - timedelta(hours=3),
        point_value=50.0,
        created_by_id=user.id
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    # Create assignment
    assignment = TaskAssignment(task_id=task.id, user_id=user.id)
    db_session.add(assignment)
    await db_session.commit()
    
    # Run deadline enforcement first time
    result1 = await _check_deadline_penalties_async()
    assert result1["penalties_applied"] == 1
    
    # Verify points after first run
    await db_session.refresh(user)
    points_after_first = float(user.points)
    assert points_after_first == 200.0
    
    # Run deadline enforcement second time
    result2 = await _check_deadline_penalties_async()
    
    # Verify no additional penalty was applied
    assert result2["penalties_applied"] == 0
    
    # Verify points unchanged
    await db_session.refresh(user)
    assert float(user.points) == points_after_first


@pytest.mark.asyncio
async def test_deadline_enforcement_multiple_users(db_session: AsyncSession):
    """Test deadline enforcement with multiple users on same task"""
    # Create users
    user1 = User(
        email="user1@example.com",
        hashed_password="hashed",
        full_name="User 1",
        role=UserRole.TEAM_MEMBER,
        user_type=UserType.TEAM_MEMBER,
        points=150.0
    )
    user2 = User(
        email="user2@example.com",
        hashed_password="hashed",
        full_name="User 2",
        role=UserRole.TEAM_MEMBER,
        user_type=UserType.TEAM_MEMBER,
        points=250.0
    )
    db_session.add_all([user1, user2])
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)
    
    # Create overdue task
    task = Task(
        title="Multi-User Task",
        description="Test task",
        assigned_to_group=AssignedGroup.TEAM_MEMBERS,
        deadline=datetime.utcnow() - timedelta(hours=1),
        point_value=50.0,
        created_by_id=user1.id
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    # Create assignments for both users
    assignment1 = TaskAssignment(task_id=task.id, user_id=user1.id)
    assignment2 = TaskAssignment(task_id=task.id, user_id=user2.id)
    db_session.add_all([assignment1, assignment2])
    
    # User1 submits, user2 does not
    submission = TaskSubmission(
        task_id=task.id,
        user_id=user1.id,
        submission_text="User 1 submission"
    )
    db_session.add(submission)
    await db_session.commit()
    
    # Run deadline enforcement
    result = await _check_deadline_penalties_async()
    
    # Verify only user2 was penalized
    assert result["penalties_applied"] == 1
    
    # Verify user1 points unchanged
    await db_session.refresh(user1)
    assert float(user1.points) == 150.0
    
    # Verify user2 points deducted
    await db_session.refresh(user2)
    assert float(user2.points) == 150.0


@pytest.mark.asyncio
async def test_leaderboard_cache_refresh_empty(db_session: AsyncSession):
    """Test leaderboard cache refresh with no users"""
    result = await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    assert result["status"] == "completed"
    assert result["users_updated"] == 0


@pytest.mark.asyncio
async def test_leaderboard_cache_refresh_with_users(db_session: AsyncSession):
    """Test leaderboard cache refresh with multiple users"""
    # Create users with different points
    users = [
        User(
            email=f"user{i}@example.com",
            hashed_password="hashed",
            full_name=f"User {i}",
            role=UserRole.TEAM_MEMBER,
            user_type=UserType.TEAM_MEMBER,
            points=float(100 * i)
        )
        for i in range(1, 4)
    ]
    db_session.add_all(users)
    await db_session.commit()
    
    # Refresh leaderboard cache
    result = await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    assert result["status"] == "completed"
    assert result["users_updated"] == 3
    assert result["team_members"] == 3
    assert result["ambassadors"] == 0
    
    # Verify rankings are correct
    cache_result = await db_session.execute(
        select(LeaderboardCache).order_by(LeaderboardCache.rank.asc())
    )
    cache_entries = cache_result.scalars().all()
    
    assert len(cache_entries) == 3
    assert cache_entries[0].rank == 1
    assert float(cache_entries[0].total_pp) == 300.0
    assert cache_entries[1].rank == 2
    assert float(cache_entries[1].total_pp) == 200.0
    assert cache_entries[2].rank == 3
    assert float(cache_entries[2].total_pp) == 100.0


@pytest.mark.asyncio
async def test_leaderboard_cache_updates_after_points_change(db_session: AsyncSession):
    """Test that leaderboard cache updates correctly after points change"""
    # Create users
    user1 = User(
        email="leader1@example.com",
        hashed_password="hashed",
        full_name="Leader 1",
        role=UserRole.TEAM_MEMBER,
        user_type=UserType.TEAM_MEMBER,
        points=100.0
    )
    user2 = User(
        email="leader2@example.com",
        hashed_password="hashed",
        full_name="Leader 2",
        role=UserRole.TEAM_MEMBER,
        user_type=UserType.TEAM_MEMBER,
        points=200.0
    )
    db_session.add_all([user1, user2])
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)
    
    # Initial cache refresh
    await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    # Verify initial rankings
    cache_result = await db_session.execute(
        select(LeaderboardCache).where(LeaderboardCache.user_id == user1.id)
    )
    user1_cache = cache_result.scalar_one()
    assert user1_cache.rank == 2
    
    # Award bonus points to user1
    await PointsService.award_bonus_points(
        db=db_session,
        user_id=user1.id,
        amount=150.0,
        reason="Test bonus",
        admin_id=user1.id
    )
    
    # Refresh cache
    await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    # Verify rankings updated
    cache_result = await db_session.execute(
        select(LeaderboardCache).where(LeaderboardCache.user_id == user1.id)
    )
    user1_cache = cache_result.scalar_one()
    assert user1_cache.rank == 1
    assert float(user1_cache.total_pp) == 250.0


@pytest.mark.asyncio
async def test_integrated_workflow_deadline_and_leaderboard(db_session: AsyncSession):
    """Test integrated workflow: deadline penalty affects leaderboard"""
    # Create users
    user1 = User(
        email="workflow1@example.com",
        hashed_password="hashed",
        full_name="Workflow User 1",
        role=UserRole.AMBASSADOR,
        user_type=UserType.AMBASSADOR,
        points=300.0
    )
    user2 = User(
        email="workflow2@example.com",
        hashed_password="hashed",
        full_name="Workflow User 2",
        role=UserRole.AMBASSADOR,
        user_type=UserType.AMBASSADOR,
        points=250.0
    )
    db_session.add_all([user1, user2])
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)
    
    # Initial leaderboard refresh
    await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    # Verify initial rankings
    cache_result = await db_session.execute(
        select(LeaderboardCache).where(LeaderboardCache.user_id == user1.id)
    )
    user1_initial = cache_result.scalar_one()
    assert user1_initial.rank == 1
    
    # Create overdue task for user1
    task = Task(
        title="Workflow Task",
        description="Test task",
        assigned_to_group=AssignedGroup.AMBASSADORS,
        deadline=datetime.utcnow() - timedelta(hours=1),
        point_value=50.0,
        created_by_id=user1.id
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    # Assign to user1 only
    assignment = TaskAssignment(task_id=task.id, user_id=user1.id)
    db_session.add(assignment)
    await db_session.commit()
    
    # Run deadline enforcement
    penalty_result = await _check_deadline_penalties_async()
    assert penalty_result["penalties_applied"] == 1
    
    # Refresh leaderboard
    await LeaderboardService.refresh_leaderboard_cache(db_session)
    
    # Verify rankings changed
    cache_result = await db_session.execute(
        select(LeaderboardCache).where(LeaderboardCache.user_id == user1.id)
    )
    user1_after = cache_result.scalar_one()
    assert user1_after.rank == 2  # Should now be rank 2
    assert float(user1_after.total_pp) == 200.0
    
    cache_result = await db_session.execute(
        select(LeaderboardCache).where(LeaderboardCache.user_id == user2.id)
    )
    user2_after = cache_result.scalar_one()
    assert user2_after.rank == 1  # Should now be rank 1
