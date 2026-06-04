"""Initial schema with users, tasks, and task_assignments

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE user_role AS ENUM ('Overall_Admin', 'Ambassador_Admin', 'Team_Member', 'Ambassador')")
    op.execute("CREATE TYPE user_type AS ENUM ('Team_Member', 'Ambassador')")
    op.execute("CREATE TYPE assigned_group AS ENUM ('Team_Members', 'Ambassadors', 'All')")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('Overall_Admin', 'Ambassador_Admin', 'Team_Member', 'Ambassador', 
                                  name='user_role', create_type=False), nullable=False),
        sa.Column('user_type', sa.Enum('Team_Member', 'Ambassador', 
                                       name='user_type', create_type=False), nullable=False),
        sa.Column('points', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for users table
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_user_type', 'users', ['user_type'])
    
    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('assigned_to_group', sa.Enum('Team_Members', 'Ambassadors', 'All', 
                                               name='assigned_group', create_type=False), nullable=False),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=False),
        sa.Column('point_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for tasks table
    op.create_index('ix_tasks_id', 'tasks', ['id'])
    op.create_index('ix_tasks_assigned_to_group', 'tasks', ['assigned_to_group'])
    op.create_index('ix_tasks_deadline', 'tasks', ['deadline'])
    op.create_index('ix_tasks_created_by_id', 'tasks', ['created_by_id'])
    op.create_index('ix_tasks_created_at', 'tasks', ['created_at'])
    op.create_index('ix_tasks_deleted_at', 'tasks', ['deleted_at'])
    
    # Create task_assignments table
    op.create_table(
        'task_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('task_id', 'user_id', name='uq_task_user_assignment'),
    )
    
    # Create indexes for task_assignments table
    op.create_index('ix_task_assignments_id', 'task_assignments', ['id'])
    op.create_index('ix_task_assignments_task_id', 'task_assignments', ['task_id'])
    op.create_index('ix_task_assignments_user_id', 'task_assignments', ['user_id'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('task_assignments')
    op.drop_table('tasks')
    op.drop_table('users')
    
    # Drop enum types
    op.execute("DROP TYPE assigned_group")
    op.execute("DROP TYPE user_type")
    op.execute("DROP TYPE user_role")
