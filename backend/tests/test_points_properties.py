"""Property-based tests for points system

This module contains property-based tests using Hypothesis to verify
the correctness of the points system across a wide range of inputs.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from hypothesis import given, strategies as st, assume, settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User, UserType, UserRole, Task, TaskSubmission, SubmissionStatus,
    PointsTransaction, TransactionType, AssignedGroup
)
from app.services.points_service import PointsService


# Custom strategies for generating test data
@st.composite
def user_strategy(draw, user_type=None):
    """Generate a valid user for testing"""
    if user_type is None:
        user_type = draw(st.sampled_from([UserType.TEAM_MEMBER, UserType.AMBASSADOR]))
    
    # Map user type to appropriate role
    if user_type == UserType.TEAM_MEMBER:
        role = UserRole.TEAM_MEMBER
    else:
        role = UserRole.AMBASSADOR
    
    return {
        "name": draw(st.text(min_size=1, max_size=100)),
        "email": f"{draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Nd'))))}@test.com",
        "password_hash": "hashed_password",
        "role": role,
        "user_type": user_type,
        "points": draw(st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False))
    }


@st.composite
def task_strategy(draw, creator_id):
    """Generate a valid task for testing"""
    return {
        "title": draw(st.text(min_size=1, max_size=100)),
        "description": draw(st.text(min_size=1, max_size=500)),
        "assigned_to_group": draw(st.sampled_from([AssignedGroup.TEAM_MEMBERS, AssignedGroup.AMBASSADORS, AssignedGroup.ALL])),
        "deadline": datetime.utcnow() + timedelta(days=draw(st.integers(min_value=1, max_value=30))),
        "point_value": draw(st.floats(min_value=1, max_value=500, allow_nan=False, allow_infinity=False)),
        "created_by_id": creator_id
    }


@st.composite
def submission_strategy(draw, task_id, user_id):
    """Generate a valid submission for testing"""
    return {
        "task_id": task_id,
        "user_id": user_id,
        "content": draw(st.text(min_size=1, max_size=1000)),
        "status": SubmissionStatus.PENDING
    }


# Helper functions
async def create_test_user(db: AsyncSession, **kwargs) -> User:
    """Create a test user in the database"""
    user = User(**kwargs)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_test_task(db: AsyncSession, **kwargs) -> Task:
    """Create a test task in the database"""
    task = Task(**kwargs)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def create_test_submission(db: AsyncSession, **kwargs) -> TaskSubmission:
    """Create a test submission in the database"""
    submission = TaskSubmission(**kwargs)
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


# Property 12: Team Member Reward Calculation
@pytest.mark.asyncio
@given(user_data=user_strategy(user_type=UserType.TEAM_MEMBER))
@settings(max_examples=10, deadline=None)
async def test_property_12_team_member_reward_calculation(db_session: AsyncSession, user_data):
    """
    **Validates: Requirements 5.1**
    
    Property 12: Team Member Reward Calculation
    For any Team_Member submission approved by an admin, the user's PP balance 
    SHALL increase by exactly 50 PP, and a points_transaction record SHALL be 
    created with transaction_type "Task_Approval".
    """
    # Create admin user
    admin = await create_test_user(
        db_session,
        name="Admin User",
        email=f"admin_{uuid.uuid4().hex[:8]}@test.com",
        password_hash="hashed",
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    
    # Create team member user
    user = await create_test_user(db_session, **user_data)
    initial_points = float(user.points)
    
    # Create task
    task = await create_test_task(
        db_session,
        title="Test Task",
        description="Test Description",
        assigned_to_group=AssignedGroup.TEAM_MEMBERS,
        deadline=datetime.utcnow() + timedelta(days=7),
        point_value=50.0,
        created_by_id=admin.id
    )
    
    # Create submission
    submission = await create_test_submission(
        db_session,
        task_id=task.id,
        user_id=user.id,
        content="Test submission content",
        status=SubmissionStatus.PENDING
    )
    
    # Award task approval reward
    transaction = await PointsService.award_task_approval_reward(
        db=db_session,
        submission_id=submission.id
    )
    
    # Verify transaction was created with correct type
    assert transaction.transaction_type == TransactionType.TASK_APPROVAL
    assert transaction.user_id == user.id
    assert float(transaction.amount) == 50.0
    
    # Verify user's PP balance increased by exactly 50
    await db_session.refresh(user)
    final_points = float(user.points)
    assert final_points == initial_points + 50.0
    
    # Verify points_transaction record exists
    result = await db_session.execute(
        select(PointsTransaction).where(
            PointsTransaction.user_id == user.id,
            PointsTransaction.transaction_type == TransactionType.TASK_APPROVAL,
            PointsTransaction.related_submission_id == submission.id
        )
    )
    db_transaction = result.scalar_one()
    assert db_transaction is not None
    assert float(db_transaction.amount) == 50.0


# Property 13: Ambassador Reward Calculation
@pytest.mark.asyncio
@given(user_data=user_strategy(user_type=UserType.AMBASSADOR))
@settings(max_examples=10, deadline=None)
async def test_property_13_ambassador_reward_calculation(db_session: AsyncSession, user_data):
    """
    **Validates: Requirements 5.2**
    
    Property 13: Ambassador Reward Calculation
    For any Ambassador submission approved by an admin, the user's PP balance 
    SHALL increase by exactly 138.6 PP, and a points_transaction record SHALL 
    be created with transaction_type "Task_Approval".
    """
    # Create admin user
    admin = await create_test_user(
        db_session,
        name="Admin User",
        email=f"admin_{uuid.uuid4().hex[:8]}@test.com",
        password_hash="hashed",
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    
    # Create ambassador user
    user = await create_test_user(db_session, **user_data)
    initial_points = float(user.points)
    
    # Create task
    task = await create_test_task(
        db_session,
        title="Test Task",
        description="Test Description",
        assigned_to_group=AssignedGroup.AMBASSADORS,
        deadline=datetime.utcnow() + timedelta(days=7),
        point_value=138.6,
        created_by_id=admin.id
    )
    
    # Create submission
    submission = await create_test_submission(
        db_session,
        task_id=task.id,
        user_id=user.id,
        content="Test submission content",
        status=SubmissionStatus.PENDING
    )
    
    # Award task approval reward
    transaction = await PointsService.award_task_approval_reward(
        db=db_session,
        submission_id=submission.id
    )
    
    # Verify transaction was created with correct type
    assert transaction.transaction_type == TransactionType.TASK_APPROVAL
    assert transaction.user_id == user.id
    assert float(transaction.amount) == 138.6
    
    # Verify user's PP balance increased by exactly 138.6
    await db_session.refresh(user)
    final_points = float(user.points)
    assert abs(final_points - (initial_points + 138.6)) < 0.01  # Allow small floating point error
    
    # Verify points_transaction record exists
    result = await db_session.execute(
        select(PointsTransaction).where(
            PointsTransaction.user_id == user.id,
            PointsTransaction.transaction_type == TransactionType.TASK_APPROVAL,
            PointsTransaction.related_submission_id == submission.id
        )
    )
    db_transaction = result.scalar_one()
    assert db_transaction is not None
    assert float(db_transaction.amount) == 138.6


# Property 14: Deadline Penalty Calculation
@pytest.mark.asyncio
@given(user_data=user_strategy())
@settings(max_examples=10, deadline=None)
async def test_property_14_deadline_penalty_calculation(db_session: AsyncSession, user_data):
    """
    **Validates: Requirements 5.3**
    
    Property 14: Deadline Penalty Calculation
    For any missed deadline, the user's PP balance SHALL decrease by exactly 100 PP, 
    and a points_transaction record SHALL be created with transaction_type "Deadline_Penalty".
    """
    # Ensure user has enough points to deduct
    user_data["points"] = max(float(user_data["points"]), 100.0)
    
    # Create admin user
    admin = await create_test_user(
        db_session,
        name="Admin User",
        email=f"admin_{uuid.uuid4().hex[:8]}@test.com",
        password_hash="hashed",
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    
    # Create user
    user = await create_test_user(db_session, **user_data)
    initial_points = float(user.points)
    
    # Create task with past deadline
    task = await create_test_task(
        db_session,
        title="Test Task",
        description="Test Description",
        assigned_to_group=AssignedGroup.TEAM_MEMBERS,
        deadline=datetime.utcnow() - timedelta(days=1),  # Past deadline
        point_value=50.0,
        created_by_id=admin.id
    )
    
    # Apply deadline penalty
    transaction = await PointsService.apply_deadline_penalty(
        db=db_session,
        user_id=user.id,
        task_id=task.id
    )
    
    # Verify transaction was created with correct type
    assert transaction.transaction_type == TransactionType.DEADLINE_PENALTY
    assert transaction.user_id == user.id
    assert float(transaction.amount) == -100.0
    
    # Verify user's PP balance decreased by exactly 100
    await db_session.refresh(user)
    final_points = float(user.points)
    assert final_points == initial_points - 100.0
    
    # Verify points_transaction record exists
    result = await db_session.execute(
        select(PointsTransaction).where(
            PointsTransaction.user_id == user.id,
            PointsTransaction.transaction_type == TransactionType.DEADLINE_PENALTY,
            PointsTransaction.related_task_id == task.id
        )
    )
    db_transaction = result.scalar_one()
    assert db_transaction is not None
    assert float(db_transaction.amount) == -100.0


# Property 15: Admin Bonus Points
@pytest.mark.asyncio
@given(
    user_data=user_strategy(),
    bonus_amount=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=10, deadline=None)
async def test_property_15_admin_bonus_points(db_session: AsyncSession, user_data, bonus_amount):
    """
    **Validates: Requirements 5.4**
    
    Property 15: Admin Bonus Points
    For any admin bonus operation with a specified amount, the user's PP balance 
    SHALL increase by exactly that amount, and a points_transaction record SHALL 
    be created with transaction_type "Admin_Bonus".
    """
    # Create user
    user = await create_test_user(db_session, **user_data)
    initial_points = float(user.points)
    
    # Apply admin bonus
    transaction = await PointsService.assign_admin_bonus(
        db=db_session,
        user_id=user.id,
        amount=bonus_amount,
        reason="Test bonus",
        admin_role=UserRole.OVERALL_ADMIN
    )
    
    # Verify transaction was created with correct type
    assert transaction.transaction_type == TransactionType.ADMIN_BONUS
    assert transaction.user_id == user.id
    assert abs(float(transaction.amount) - bonus_amount) < 0.01
    
    # Verify user's PP balance increased by exactly the bonus amount
    await db_session.refresh(user)
    final_points = float(user.points)
    assert abs(final_points - (initial_points + bonus_amount)) < 0.01
    
    # Verify points_transaction record exists
    result = await db_session.execute(
        select(PointsTransaction).where(
            PointsTransaction.user_id == user.id,
            PointsTransaction.transaction_type == TransactionType.ADMIN_BONUS
        )
    )
    db_transaction = result.scalar_one()
    assert db_transaction is not None
    assert abs(float(db_transaction.amount) - bonus_amount) < 0.01


# Property 16: Admin Penalty Points
@pytest.mark.asyncio
@given(
    user_data=user_strategy(),
    penalty_amount=st.floats(min_value=1.0, max_value=500.0, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=10, deadline=None)
async def test_property_16_admin_penalty_points(db_session: AsyncSession, user_data, penalty_amount):
    """
    **Validates: Requirements 5.5**
    
    Property 16: Admin Penalty Points
    For any admin penalty operation with a specified amount, the user's PP balance 
    SHALL decrease by exactly that amount, and a points_transaction record SHALL 
    be created with transaction_type "Admin_Penalty".
    """
    # Ensure user has enough points to deduct
    user_data["points"] = max(float(user_data["points"]), penalty_amount + 100.0)
    
    # Create user
    user = await create_test_user(db_session, **user_data)
    initial_points = float(user.points)
    
    # Apply admin penalty
    transaction = await PointsService.apply_admin_penalty(
        db=db_session,
        user_id=user.id,
        amount=penalty_amount,
        reason="Test penalty",
        admin_role=UserRole.OVERALL_ADMIN
    )
    
    # Verify transaction was created with correct type
    assert transaction.transaction_type == TransactionType.ADMIN_PENALTY
    assert transaction.user_id == user.id
    assert abs(float(transaction.amount) - (-penalty_amount)) < 0.01
    
    # Verify user's PP balance decreased by exactly the penalty amount
    await db_session.refresh(user)
    final_points = float(user.points)
    assert abs(final_points - (initial_points - penalty_amount)) < 0.01
    
    # Verify points_transaction record exists
    result = await db_session.execute(
        select(PointsTransaction).where(
            PointsTransaction.user_id == user.id,
            PointsTransaction.transaction_type == TransactionType.ADMIN_PENALTY
        )
    )
    db_transaction = result.scalar_one()
    assert db_transaction is not None
    assert abs(float(db_transaction.amount) - (-penalty_amount)) < 0.01


# Property 17: Points Transaction History Completeness
@pytest.mark.asyncio
@given(
    user_data=user_strategy(),
    operation_type=st.sampled_from(["bonus", "penalty"])
)
@settings(max_examples=10, deadline=None)
async def test_property_17_points_transaction_history_completeness(
    db_session: AsyncSession, user_data, operation_type
):
    """
    **Validates: Requirements 5.6**
    
    Property 17: Points Transaction History Completeness
    For any PP change to a user's balance, a corresponding points_transaction record 
    SHALL exist with the correct user_id, amount, transaction_type, and timestamp.
    """
    # Create user
    user = await create_test_user(db_session, **user_data)
    
    # Perform operation
    if operation_type == "bonus":
        amount = 100.0
        transaction = await PointsService.assign_admin_bonus(
            db=db_session,
            user_id=user.id,
            amount=amount,
            reason="Test bonus",
            admin_role=UserRole.OVERALL_ADMIN
        )
        expected_type = TransactionType.ADMIN_BONUS
    else:  # penalty
        amount = 50.0
        transaction = await PointsService.apply_admin_penalty(
            db=db_session,
            user_id=user.id,
            amount=amount,
            reason="Test penalty",
            admin_role=UserRole.OVERALL_ADMIN
        )
        expected_type = TransactionType.ADMIN_PENALTY
        amount = -amount  # Penalty is stored as negative
    
    # Verify transaction record exists with correct fields
    result = await db_session.execute(
        select(PointsTransaction).where(PointsTransaction.id == transaction.id)
    )
    db_transaction = result.scalar_one()
    
    assert db_transaction.user_id == user.id
    assert abs(float(db_transaction.amount) - amount) < 0.01
    assert db_transaction.transaction_type == expected_type
    assert db_transaction.created_at is not None
    assert isinstance(db_transaction.created_at, datetime)


# Property 18: Reward Allocation Idempotency
@pytest.mark.asyncio
@given(user_data=user_strategy(user_type=UserType.TEAM_MEMBER))
@settings(max_examples=10, deadline=None)
async def test_property_18_reward_allocation_idempotency(db_session: AsyncSession, user_data):
    """
    **Validates: Requirements 5.7**
    
    Property 18: Reward Allocation Idempotency
    For any task submission approval, the reward SHALL be allocated exactly once, 
    and attempting to approve the same submission again SHALL not result in 
    additional PP being awarded.
    """
    # Create admin user
    admin = await create_test_user(
        db_session,
        name="Admin User",
        email=f"admin_{uuid.uuid4().hex[:8]}@test.com",
        password_hash="hashed",
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    
    # Create user
    user = await create_test_user(db_session, **user_data)
    initial_points = float(user.points)
    
    # Create task
    task = await create_test_task(
        db_session,
        title="Test Task",
        description="Test Description",
        assigned_to_group=AssignedGroup.TEAM_MEMBERS,
        deadline=datetime.utcnow() + timedelta(days=7),
        point_value=50.0,
        created_by_id=admin.id
    )
    
    # Create submission
    submission = await create_test_submission(
        db_session,
        task_id=task.id,
        user_id=user.id,
        content="Test submission content",
        status=SubmissionStatus.PENDING
    )
    
    # Award task approval reward (first time)
    transaction1 = await PointsService.award_task_approval_reward(
        db=db_session,
        submission_id=submission.id
    )
    
    # Verify first reward was applied
    await db_session.refresh(user)
    points_after_first = float(user.points)
    assert points_after_first == initial_points + 50.0
    
    # Attempt to award reward again (should fail)
    with pytest.raises(ValueError, match="already been rewarded"):
        await PointsService.award_task_approval_reward(
            db=db_session,
            submission_id=submission.id
        )
    
    # Verify points did not change after second attempt
    await db_session.refresh(user)
    points_after_second = float(user.points)
    assert points_after_second == points_after_first
    
    # Verify only one transaction exists for this submission
    result = await db_session.execute(
        select(PointsTransaction).where(
            PointsTransaction.user_id == user.id,
            PointsTransaction.transaction_type == TransactionType.TASK_APPROVAL,
            PointsTransaction.related_submission_id == submission.id
        )
    )
    transactions = result.scalars().all()
    assert len(transactions) == 1
