"""Add points transaction and audit logging models

Revision ID: 003
Revises: 002
Create Date: 2024-01-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE transaction_type AS ENUM ('Task_Approval', 'Deadline_Penalty', 'Admin_Bonus', 'Admin_Penalty')")
    op.execute("CREATE TYPE audit_action_type AS ENUM ('Create', 'Update', 'Delete', 'Approve', 'Reject', 'Assign_Points', 'Deduct_Points', 'Reset_Password')")
    
    # Create points_transactions table
    op.create_table(
        'points_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('transaction_type', sa.Enum('Task_Approval', 'Deadline_Penalty', 'Admin_Bonus', 'Admin_Penalty',
                                              name='transaction_type', create_type=False), nullable=False),
        sa.Column('reason', sa.String(255), nullable=False),
        sa.Column('related_task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_submission_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['related_task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['related_submission_id'], ['task_submissions.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for points_transactions table
    op.create_index('ix_points_transactions_id', 'points_transactions', ['id'])
    op.create_index('ix_points_transactions_user_id', 'points_transactions', ['user_id'])
    op.create_index('ix_points_transactions_transaction_type', 'points_transactions', ['transaction_type'])
    op.create_index('ix_points_transactions_related_task_id', 'points_transactions', ['related_task_id'])
    op.create_index('ix_points_transactions_related_submission_id', 'points_transactions', ['related_submission_id'])
    op.create_index('ix_points_transactions_created_at', 'points_transactions', ['created_at'])
    
    # Create deadline_penalties_applied table
    op.create_table(
        'deadline_penalties_applied',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('penalty_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('task_id', 'user_id', name='uq_deadline_penalty'),
    )
    
    # Create indexes for deadline_penalties_applied table
    op.create_index('ix_deadline_penalties_applied_id', 'deadline_penalties_applied', ['id'])
    op.create_index('ix_deadline_penalties_applied_task_id', 'deadline_penalties_applied', ['task_id'])
    op.create_index('ix_deadline_penalties_applied_user_id', 'deadline_penalties_applied', ['user_id'])
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('admin_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.Enum('Create', 'Update', 'Delete', 'Approve', 'Reject', 'Assign_Points', 'Deduct_Points', 'Reset_Password',
                                    name='audit_action_type', create_type=False), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('changes', postgresql.JSONB, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['admin_user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for audit_logs table
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'])
    op.create_index('ix_audit_logs_admin_user_id', 'audit_logs', ['admin_user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('audit_logs')
    op.drop_table('deadline_penalties_applied')
    op.drop_table('points_transactions')
    
    # Drop enum types
    op.execute("DROP TYPE audit_action_type")
    op.execute("DROP TYPE transaction_type")
