"""Add submission and file storage models

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE submission_status AS ENUM ('Pending', 'Approved', 'Rejected')")
    op.execute("CREATE TYPE file_scan_status AS ENUM ('Pending', 'Scanned', 'Infected', 'Failed')")
    
    # Create task_submissions table
    op.create_table(
        'task_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('status', sa.Enum('Pending', 'Approved', 'Rejected', 
                                    name='submission_status', create_type=False), 
                  nullable=False, server_default='Pending'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('reviewed_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('task_id', 'user_id', name='uq_task_user_submission'),
    )
    
    # Create indexes for task_submissions table
    op.create_index('ix_task_submissions_id', 'task_submissions', ['id'])
    op.create_index('ix_task_submissions_task_id', 'task_submissions', ['task_id'])
    op.create_index('ix_task_submissions_user_id', 'task_submissions', ['user_id'])
    op.create_index('ix_task_submissions_status', 'task_submissions', ['status'])
    op.create_index('ix_task_submissions_submitted_at', 'task_submissions', ['submitted_at'])
    op.create_index('ix_task_submissions_reviewed_by_id', 'task_submissions', ['reviewed_by_id'])
    
    # Create submission_files table
    op.create_table(
        'submission_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_size', sa.Integer, nullable=False),
        sa.Column('file_data', sa.LargeBinary, nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('scan_status', sa.Enum('Pending', 'Scanned', 'Infected', 'Failed', 
                                         name='file_scan_status', create_type=False), 
                  nullable=False, server_default='Pending'),
        sa.Column('scan_error', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['submission_id'], ['task_submissions.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for submission_files table
    op.create_index('ix_submission_files_id', 'submission_files', ['id'])
    op.create_index('ix_submission_files_submission_id', 'submission_files', ['submission_id'])
    op.create_index('ix_submission_files_scan_status', 'submission_files', ['scan_status'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('submission_files')
    op.drop_table('task_submissions')
    
    # Drop enum types
    op.execute("DROP TYPE file_scan_status")
    op.execute("DROP TYPE submission_status")
