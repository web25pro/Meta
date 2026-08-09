"""Points transaction and audit logging models"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Text, Numeric, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint, Integer, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TransactionType(str, Enum):
    """Points transaction type enumeration"""
    TASK_APPROVAL = "Task_Approval"
    DEADLINE_PENALTY = "Deadline_Penalty"
    ADMIN_BONUS = "Admin_Bonus"
    ADMIN_PENALTY = "Admin_Penalty"
    QUEST_REWARD = "Quest_Reward"
    CAMPAIGN_REWARD = "Campaign_Reward"


class PPLedgerEntry(Base):
    """Canonical immutable record of a Panda Points movement.

    ``PointsTransaction`` remains as a compatibility projection for the legacy
    API. New economic code should write this ledger through ``PointsService``.
    """

    __tablename__ = "pp_ledger_entries"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_pp_ledger_idempotency_key"),
        Index("ix_pp_ledger_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    bucket: Mapped[str] = mapped_column(String(32), nullable=False, default="available")
    transaction_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="posted")
    entry_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class IdempotencyKey(Base):
    """Persistent request replay record for mutating API operations."""

    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_idempotency_user_key"),
        Index("ix_idempotency_expires_at", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    body_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_json: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    response_content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    processing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditActionType(str, Enum):
    """Audit action type enumeration"""
    CREATE = "Create"
    UPDATE = "Update"
    DELETE = "Delete"
    APPROVE = "Approve"
    REJECT = "Reject"
    ASSIGN_POINTS = "Assign_Points"
    DEDUCT_POINTS = "Deduct_Points"
    RESET_PASSWORD = "Reset_Password"


class PointsTransaction(Base):
    """
    PointsTransaction model for immutable transaction log of all PP changes.
    
    Attributes:
        id: Unique identifier (UUID)
        user_id: ID of the user whose points changed
        amount: Points amount (positive or negative)
        transaction_type: Type of transaction
        reason: Human-readable reason for the transaction
        related_task_id: ID of related task (if applicable)
        related_submission_id: ID of related submission (if applicable)
        created_at: Timestamp of transaction
    """
    __tablename__ = "points_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLEnum(
            TransactionType,
            name="transaction_type",
            create_type=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    related_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    related_submission_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task_submissions.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="points_transactions",
        foreign_keys=[user_id]
    )

    def __repr__(self) -> str:
        return f"<PointsTransaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, type={self.transaction_type})>"


class DeadlinePenaltyApplied(Base):
    """
    DeadlinePenaltyApplied model for tracking applied deadline penalties to prevent duplicates.
    
    Attributes:
        id: Unique identifier (UUID)
        task_id: ID of the task with missed deadline
        user_id: ID of the user who missed the deadline
        penalty_amount: Amount of penalty applied
        applied_at: Timestamp of penalty application
    """
    __tablename__ = "deadline_penalties_applied"
    __table_args__ = (
        UniqueConstraint("task_id", "user_id", name="uq_deadline_penalty"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    penalty_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<DeadlinePenaltyApplied(task_id={self.task_id}, user_id={self.user_id})>"


class AuditLog(Base):
    """
    AuditLog model for immutable audit trail of administrative actions.
    
    Attributes:
        id: Unique identifier (UUID)
        admin_user_id: ID of the admin who performed the action
        action: Type of action performed
        resource_type: Type of resource affected (User, Task, Submission, etc.)
        resource_id: ID of the affected resource
        changes: JSON object containing before/after values
        ip_address: IP address of the request
        user_agent: User agent of the request
        created_at: Timestamp of the action
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    admin_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    action: Mapped[AuditActionType] = mapped_column(
        SQLEnum(
            AuditActionType,
            name="audit_action_type",
            create_type=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True
    )
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    changes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    # Relationships
    admin_user: Mapped["User"] = relationship(
        "User",
        back_populates="audit_logs",
        foreign_keys=[admin_user_id]
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, resource_type={self.resource_type})>"
