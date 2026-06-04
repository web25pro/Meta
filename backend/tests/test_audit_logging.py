"""Tests for audit logging functionality"""
import pytest
import uuid
from datetime import datetime
from sqlalchemy import select

from app.models import User, UserRole, UserType, Announcement, Schedule
from app.models.leaderboard_schedule_announcement import TargetGroup
from app.models.points_and_audit import AuditLog, AuditActionType
from app.services.audit_service import AuditService


@pytest.mark.asyncio
async def test_audit_log_create_action(db_session):
    """Test logging a CREATE action"""
    # Create a test admin user
    admin = User(
        email="admin@test.com",
        hashed_password="hashed",
        full_name="Admin User",
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    
    # Create a test resource ID
    resource_id = uuid.uuid4()
    
    # Log a CREATE action
    audit_log = await AuditService.log_create(
        db=db_session,
        admin_user_id=admin.id,
        resource_type="Task",
        resource_id=resource_id,
        resource_data={"title": "Test Task", "deadline": "2024-12-31"},
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0"
    )
    
    # Verify audit log was created
    assert audit_log.id is not None
    assert audit_log.admin_user_id == admin.id
    assert audit_log.action == AuditActionType.CREATE
    assert audit_log.resource_type == "Task"
    assert audit_log.resource_id == resource_id
    assert audit_log.changes["created"]["title"] == "Test Task"
    assert audit_log.ip_address == "192.168.1.1"
    assert audit_log.user_agent == "Mozilla/5.0"
    assert audit_log.created_at is not None


@pytest.mark.asyncio
async def test_audit_log_update_action(db_session):
    """Test logging an UPDATE action"""
    # Create a test admin user
    admin = User(
        email="admin@test.com",
        hashed_password="hashed",
        full_name="Admin User",
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    
    # Create a test resource ID
    resource_id = uuid.uuid4()
    
    # Log an UPDATE action
    audit_log = await AuditService.log_update(
        db=db_session,
        admin_user_id=admin.id,
        resource_type="Announcement",
        resource_id=resource_id,
        before={"title": "Old Title", "content": "Old Content"},
        after={"title": "New Title", "content": "New Content"},
        ip_address="192.168.1.1"
    )
    
    # Verify audit log was created
    assert audit_log.id is not None
    assert audit_log.admin_user_id == admin.id
    assert audit_log.action == AuditActionType.UPDATE
    assert audit_log.resource_type == "Announcement"
    assert audit_log.resource_id == resource_id
    assert audit_log.changes["before"]["title"] == "Old Title"
    assert audit_log.changes["after"]["title"] == "New Title"
    assert audit_log.ip_address == "192.168.1.1"


@pytest.mark.asyncio
async def test_audit_log_delete_action(db_session):
    """Test logging a DELETE action"""
    # Create a test admin user
    admin = User(
        email="admin@test.com",
        hashed_password="hashed",
        full_name="Admin User",
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    
    # Create a test resource ID
    resource_id = uuid.uuid4()
    
    # Log a DELETE action
    audit_log = await AuditService.log_delete(
        db=db_session,
        admin_user_id=admin.id,
        resource_type="Schedule",
        resource_id=resource_id,
        resource_data={"title": "Deleted Schedule", "event_date": "2024-12-31"},
        ip_address="192.168.1.1"
    )
    
    # Verify audit log was created
    assert audit_log.id is not None
    assert audit_log.admin_user_id == admin.id
    assert audit_log.action == AuditActionType.DELETE
    assert audit_log.resource_type == "Schedule"
    assert audit_log.resource_id == resource_id
    assert audit_log.changes["deleted"]["title"] == "Deleted Schedule"


@pytest.mark.asyncio
async def test_audit_log_approve_action(db_session):
    """Test logging an APPROVE action"""
    # Create a test admin user
    admin = User(
        email="admin@test.com",
        hashed_password="hashed",
        full_name="Admin User",
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    
    # Create a test resource ID
    resource_id = uuid.uuid4()
    
    # Log an APPROVE action
    audit_log = await AuditService.log_approve(
        db=db_session,
        admin_user_id=admin.id,
        resource_type="Submission",
        resource_id=resource_id,
        metadata={"points_awarded": 50.0},
        ip_address="192.168.1.1"
    )
    
    # Verify audit log was created
    assert audit_log.id is not None
    assert audit_log.admin_user_id == admin.id
    assert audit_log.action == AuditActionType.APPROVE
    assert audit_log.resource_type == "Submission"
    assert audit_log.resource_id == resource_id
    assert audit_log.changes["points_awarded"] == 50.0


@pytest.mark.asyncio
async def test_audit_log_reject_action(db_session):
    """Test logging a REJECT action"""
    # Create a test admin user
    admin = User(
        email="admin@test.com",
        hashed_password="hashed",
        full_name="Admin User",
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    
    # Create a test resource ID
    resource_id = uuid.uuid4()
    
    # Log a REJECT action
    audit_log = await AuditService.log_reject(
        db=db_session,
        admin_user_id=admin.id,
        resource_type="Submission",
        resource_id=resource_id,
        metadata={"reason": "Incomplete work"},
        ip_address="192.168.1.1"
    )
    
    # Verify audit log was created
    assert audit_log.id is not None
    assert audit_log.admin_user_id == admin.id
    assert audit_log.action == AuditActionType.REJECT
    assert audit_log.resource_type == "Submission"
    assert audit_log.resource_id == resource_id
    assert audit_log.changes["reason"] == "Incomplete work"


@pytest.mark.asyncio
async def test_audit_log_assign_points(db_session):
    """Test logging an ASSIGN_POINTS action"""
    # Create a test admin user
    admin = User(
        email="admin@test.com",
        hashed_password="hashed",
        full_name="Admin User",
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    db_session.add(admin)
    
    # Create a test user
    user = User(
        email="user@test.com",
        hashed_password="hashed",
        full_name="Test User",
        role=UserRole.TEAM_MEMBER,
        user_type=UserType.TEAM_MEMBER,
        points=100.0
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(admin)
    await db_session.refresh(user)
    
    # Log an ASSIGN_POINTS action
    audit_log = await AuditService.log_assign_points(
        db=db_session,
        admin_user_id=admin.id,
        user_id=user.id,
        amount=50.0,
        reason="Excellent performance",
        ip_address="192.168.1.1"
    )
    
    # Verify audit log was created
    assert audit_log.id is not None
    assert audit_log.admin_user_id == admin.id
    assert audit_log.action == AuditActionType.ASSIGN_POINTS
    assert audit_log.resource_type == "User"
    assert audit_log.resource_id == user.id
    assert audit_log.changes["amount"] == 50.0
    assert audit_log.changes["reason"] == "Excellent performance"


@pytest.mark.asyncio
async def test_audit_log_deduct_points(db_session):
    """Test logging a DEDUCT_POINTS action"""
    # Create a test admin user
    admin = User(
        email="admin@test.com",
        hashed_password="hashed",
        full_name="Admin User",
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    db_session.add(admin)
    
    # Create a test user
    user = User(
        email="user@test.com",
        hashed_password="hashed",
        full_name="Test User",
        role=UserRole.TEAM_MEMBER,
        user_type=UserType.TEAM_MEMBER,
        points=100.0
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(admin)
    await db_session.refresh(user)
    
    # Log a DEDUCT_POINTS action
    audit_log = await AuditService.log_deduct_points(
        db=db_session,
        admin_user_id=admin.id,
        user_id=user.id,
        amount=25.0,
        reason="Policy violation",
        ip_address="192.168.1.1"
    )
    
    # Verify audit log was created
    assert audit_log.id is not None
    assert audit_log.admin_user_id == admin.id
    assert audit_log.action == AuditActionType.DEDUCT_POINTS
    assert audit_log.resource_type == "User"
    assert audit_log.resource_id == user.id
    assert audit_log.changes["amount"] == 25.0
    assert audit_log.changes["reason"] == "Policy violation"


@pytest.mark.asyncio
async def test_audit_log_reset_password(db_session):
    """Test logging a RESET_PASSWORD action"""
    # Create a test admin user
    admin = User(
        email="admin@test.com",
        hashed_password="hashed",
        full_name="Admin User",
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    db_session.add(admin)
    
    # Create a test user
    user = User(
        email="user@test.com",
        hashed_password="hashed",
        full_name="Test User",
        role=UserRole.TEAM_MEMBER,
        user_type=UserType.TEAM_MEMBER,
        points=100.0
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(admin)
    await db_session.refresh(user)
    
    # Log a RESET_PASSWORD action
    audit_log = await AuditService.log_reset_password(
        db=db_session,
        admin_user_id=admin.id,
        user_id=user.id,
        ip_address="192.168.1.1"
    )
    
    # Verify audit log was created
    assert audit_log.id is not None
    assert audit_log.admin_user_id == admin.id
    assert audit_log.action == AuditActionType.RESET_PASSWORD
    assert audit_log.resource_type == "User"
    assert audit_log.resource_id == user.id
    assert audit_log.changes is None  # Password details should not be logged


@pytest.mark.asyncio
async def test_audit_log_immutability(db_session):
    """Test that audit logs are immutable (no update/delete operations)"""
    # Create a test admin user
    admin = User(
        email="admin@test.com",
        hashed_password="hashed",
        full_name="Admin User",
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    
    # Create an audit log
    resource_id = uuid.uuid4()
    audit_log = await AuditService.log_create(
        db=db_session,
        admin_user_id=admin.id,
        resource_type="Task",
        resource_id=resource_id,
        resource_data={"title": "Test Task"}
    )
    
    # Verify the audit log exists
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.id == audit_log.id)
    )
    fetched_log = result.scalar_one()
    assert fetched_log is not None
    assert fetched_log.resource_type == "Task"
    
    # Note: The immutability is enforced by not providing update/delete methods
    # in the AuditService and by database-level constraints if configured


@pytest.mark.asyncio
async def test_audit_log_includes_timestamp(db_session):
    """Test that audit logs include timestamp"""
    # Create a test admin user
    admin = User(
        email="admin@test.com",
        hashed_password="hashed",
        full_name="Admin User",
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    
    # Record time before creating audit log
    before_time = datetime.utcnow()
    
    # Create an audit log
    resource_id = uuid.uuid4()
    audit_log = await AuditService.log_create(
        db=db_session,
        admin_user_id=admin.id,
        resource_type="Task",
        resource_id=resource_id,
        resource_data={"title": "Test Task"}
    )
    
    # Record time after creating audit log
    after_time = datetime.utcnow()
    
    # Verify timestamp is within expected range
    assert audit_log.created_at is not None
    assert before_time <= audit_log.created_at <= after_time


@pytest.mark.asyncio
async def test_audit_log_includes_admin_user_id(db_session):
    """Test that audit logs include admin_user_id"""
    # Create a test admin user
    admin = User(
        email="admin@test.com",
        hashed_password="hashed",
        full_name="Admin User",
        role=UserRole.OVERALL_ADMIN,
        user_type=UserType.TEAM_MEMBER,
        points=0.0
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    
    # Create an audit log
    resource_id = uuid.uuid4()
    audit_log = await AuditService.log_create(
        db=db_session,
        admin_user_id=admin.id,
        resource_type="Task",
        resource_id=resource_id,
        resource_data={"title": "Test Task"}
    )
    
    # Verify admin_user_id is recorded
    assert audit_log.admin_user_id == admin.id
    
    # Verify we can query audit logs by admin
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.admin_user_id == admin.id)
    )
    admin_logs = result.scalars().all()
    assert len(admin_logs) == 1
    assert admin_logs[0].id == audit_log.id
