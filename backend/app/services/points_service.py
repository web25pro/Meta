"""Points and rewards service layer"""
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from app.models import (
    PointsTransaction, User, TaskSubmission, UserType, 
    TransactionType, UserRole
)
from app.core.rbac import Permission, has_permission
from app.services.audit_service import AuditService
from app.models.points_and_audit import AuditActionType


class PointsService:
    """Points service for business logic"""
    
    # Points configuration
    TEAM_MEMBER_TASK_REWARD = 50.0
    AMBASSADOR_TASK_REWARD = 138.6
    DEADLINE_PENALTY = -100.0
    
    @staticmethod
    async def create_transaction(
        db: AsyncSession,
        user_id: uuid.UUID,
        amount: float,
        transaction_type: TransactionType,
        reason: str,
        related_task_id: Optional[uuid.UUID] = None,
        related_submission_id: Optional[uuid.UUID] = None
    ) -> PointsTransaction:
        """
        Create a points transaction and update user balance.
        
        Args:
            db: Database session
            user_id: User ID
            amount: Points amount (positive or negative)
            transaction_type: Type of transaction
            reason: Human-readable reason
            related_task_id: Related task ID (optional)
            related_submission_id: Related submission ID (optional)
            
        Returns:
            PointsTransaction: Created transaction
        """
        # Create transaction
        transaction = PointsTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            reason=reason,
            related_task_id=related_task_id,
            related_submission_id=related_submission_id
        )
        
        db.add(transaction)
        
        # Update user points and gamification stats
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one()
        user.points += amount
        
        # Award XP if amount is positive
        if amount > 0:
            user.xp += amount
            # Update level (Simple calculation: Level = floor(XP / 1000) + 1)
            new_level = int(user.xp // 1000) + 1
            user.level = max(user.level, new_level)
            
        # Update streak and activity
        now = datetime.utcnow()
        if user.last_activity_at:
            delta = now.date() - user.last_activity_at.date()
            if delta.days == 1:
                user.current_streak += 1
            elif delta.days > 1:
                user.current_streak = 1
            # If delta.days == 0, streak stays the same (multiple activities in one day)
        else:
            user.current_streak = 1
            
        user.last_activity_at = now
        
        await db.commit()
        await db.refresh(transaction)
        
        return transaction
    
    @staticmethod
    async def award_task_approval_reward(
        db: AsyncSession,
        submission_id: uuid.UUID
    ) -> PointsTransaction:
        """
        Award points for task approval.
        
        Args:
            db: Database session
            submission_id: Submission ID
            
        Returns:
            PointsTransaction: Created transaction
            
        Raises:
            ValueError: If submission not found or already rewarded
        """
        # Get submission with user
        result = await db.execute(
            select(TaskSubmission).where(TaskSubmission.id == submission_id)
        )
        submission = result.scalar_one_or_none()
        if not submission:
            raise ValueError(f"Submission with ID {submission_id} not found")
        
        # Check if already rewarded
        result = await db.execute(
            select(PointsTransaction).where(
                PointsTransaction.related_submission_id == submission_id,
                PointsTransaction.transaction_type == TransactionType.TASK_APPROVAL
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError(f"Submission {submission_id} has already been rewarded")
        
        # Get user to determine reward amount
        result = await db.execute(
            select(User).where(User.id == submission.user_id)
        )
        user = result.scalar_one()
        
        # Determine reward amount based on user type
        if user.user_type == UserType.TEAM_MEMBER:
            amount = PointsService.TEAM_MEMBER_TASK_REWARD
        else:  # Ambassador
            amount = PointsService.AMBASSADOR_TASK_REWARD
        
        # Create transaction
        transaction = await PointsService.create_transaction(
            db=db,
            user_id=submission.user_id,
            amount=amount,
            transaction_type=TransactionType.TASK_APPROVAL,
            reason=f"Task approval reward for submission {submission_id}",
            related_task_id=submission.task_id,
            related_submission_id=submission_id
        )
        
        return transaction
    
    @staticmethod
    async def apply_deadline_penalty(
        db: AsyncSession,
        user_id: uuid.UUID,
        task_id: uuid.UUID
    ) -> PointsTransaction:
        """
        Apply deadline penalty for missed task.
        
        Args:
            db: Database session
            user_id: User ID
            task_id: Task ID
            
        Returns:
            PointsTransaction: Created transaction
        """
        # Create transaction
        transaction = await PointsService.create_transaction(
            db=db,
            user_id=user_id,
            amount=PointsService.DEADLINE_PENALTY,
            transaction_type=TransactionType.DEADLINE_PENALTY,
            reason=f"Deadline penalty for task {task_id}",
            related_task_id=task_id
        )
        
        return transaction
    
    @staticmethod
    async def assign_admin_bonus(
        db: AsyncSession,
        user_id: uuid.UUID,
        amount: float,
        reason: str,
        admin_role: UserRole,
        admin_user_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> PointsTransaction:
        """
        Assign bonus points (admin only).
        
        Args:
            db: Database session
            user_id: User ID
            amount: Bonus amount (positive)
            reason: Reason for bonus
            admin_role: Role of the admin
            admin_user_id: ID of the admin assigning points
            ip_address: Optional IP address
            user_agent: Optional user agent
            
        Returns:
            PointsTransaction: Created transaction
            
        Raises:
            PermissionError: If admin cannot assign points
            ValueError: If user not found or amount invalid
        """
        # Check permission
        if not has_permission(admin_role, Permission.ASSIGN_POINTS):
            raise PermissionError(f"Role {admin_role} does not have permission to assign points")
        
        # Validate amount
        if amount <= 0:
            raise ValueError("Bonus amount must be positive")
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Create transaction
        transaction = await PointsService.create_transaction(
            db=db,
            user_id=user_id,
            amount=amount,
            transaction_type=TransactionType.ADMIN_BONUS,
            reason=reason
        )
        
        # Log audit trail
        await AuditService.log_assign_points(
            db=db,
            admin_user_id=admin_user_id,
            user_id=user_id,
            amount=amount,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return transaction
    
    @staticmethod
    async def apply_admin_penalty(
        db: AsyncSession,
        user_id: uuid.UUID,
        amount: float,
        reason: str,
        admin_role: UserRole,
        admin_user_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> PointsTransaction:
        """
        Apply penalty points (admin only).
        
        Args:
            db: Database session
            user_id: User ID
            amount: Penalty amount (positive, will be deducted)
            reason: Reason for penalty
            admin_role: Role of the admin
            admin_user_id: ID of the admin deducting points
            ip_address: Optional IP address
            user_agent: Optional user agent
            
        Returns:
            PointsTransaction: Created transaction
            
        Raises:
            PermissionError: If admin cannot deduct points
            ValueError: If user not found or amount invalid
        """
        # Check permission
        if not has_permission(admin_role, Permission.DEDUCT_POINTS):
            raise PermissionError(f"Role {admin_role} does not have permission to deduct points")
        
        # Validate amount
        if amount <= 0:
            raise ValueError("Penalty amount must be positive")
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Create transaction (negative amount)
        transaction = await PointsService.create_transaction(
            db=db,
            user_id=user_id,
            amount=-amount,
            transaction_type=TransactionType.ADMIN_PENALTY,
            reason=reason
        )
        
        # Log audit trail
        await AuditService.log_deduct_points(
            db=db,
            admin_user_id=admin_user_id,
            user_id=user_id,
            amount=amount,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return transaction
    
    @staticmethod
    async def get_user_points(
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> float:
        """
        Get user's current points balance.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            float: Current points balance
            
        Raises:
            ValueError: If user not found
        """
        result = await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        return user.points
    
    @staticmethod
    async def get_user_transactions(
        db: AsyncSession,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[PointsTransaction], int]:
        """
        Get user's transaction history.
        
        Args:
            db: Database session
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Number of transactions per page
            
        Returns:
            tuple: (list of transactions, total count)
        """
        # Build query
        query = select(PointsTransaction).where(PointsTransaction.user_id == user_id)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(PointsTransaction.created_at.desc()).offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        return list(transactions), total
