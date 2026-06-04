"""Task submission and file storage models"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Text, Numeric, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SubmissionStatus(str, Enum):
    """Submission status enumeration"""
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class FileScanStatus(str, Enum):
    """File scan status enumeration"""
    PENDING = "Pending"
    SCANNED = "Scanned"
    INFECTED = "Infected"
    FAILED = "Failed"


class TaskSubmission(Base):
    """
    TaskSubmission model representing user submissions for tasks.
    
    Attributes:
        id: Unique identifier (UUID)
        task_id: ID of the submitted task
        user_id: ID of the submitting user
        content: Submission content (text/links)
        status: Submission status (Pending, Approved, Rejected)
        submitted_at: Timestamp of submission
        reviewed_by_id: ID of admin who reviewed (NULL if not reviewed)
        reviewed_at: Timestamp of review (NULL if not reviewed)
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "task_submissions"
    __table_args__ = (
        UniqueConstraint("task_id", "user_id", name="uq_task_user_submission"),
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
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(
        SQLEnum(SubmissionStatus, name="submission_status", create_type=True),
        nullable=False,
        default=SubmissionStatus.PENDING,
        index=True
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="submissions",
        foreign_keys=[task_id]
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="submissions",
        foreign_keys=[user_id]
    )
    reviewer: Mapped["User | None"] = relationship(
        "User",
        back_populates="reviewed_submissions",
        foreign_keys=[reviewed_by_id]
    )
    files: Mapped[list["SubmissionFile"]] = relationship(
        "SubmissionFile",
        back_populates="submission",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TaskSubmission(id={self.id}, task_id={self.task_id}, user_id={self.user_id}, status={self.status})>"


class SubmissionFile(Base):
    """
    SubmissionFile model tracking uploaded files associated with submissions.
    
    Attributes:
        id: Unique identifier (UUID)
        submission_id: ID of the associated submission
        file_name: Original file name
        file_size: File size in bytes
        file_data: Binary file data stored in PostgreSQL
        mime_type: MIME type of the file
        scan_status: Virus scan status
        scan_error: Error message if scan failed
        created_at: Timestamp of file upload
    """
    __tablename__ = "submission_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    file_data: Mapped[bytes] = mapped_column(nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    scan_status: Mapped[FileScanStatus] = mapped_column(
        SQLEnum(FileScanStatus, name="file_scan_status", create_type=True),
        nullable=False,
        default=FileScanStatus.PENDING,
        index=True
    )
    scan_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    # Relationships
    submission: Mapped["TaskSubmission"] = relationship(
        "TaskSubmission",
        back_populates="files"
    )

    def __repr__(self) -> str:
        return f"<SubmissionFile(id={self.id}, submission_id={self.submission_id}, file_name={self.file_name})>"
