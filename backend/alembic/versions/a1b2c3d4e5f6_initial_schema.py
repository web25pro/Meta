"""Initial schema with users, tasks, and task_assignments

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create users table (SQLAlchemy automatically creates user_role and user_type ENUMs here)
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('Overall_Admin', 'Ambassador_Admin', 'Team_Member', 'Ambassador', 
                                  name='user_role'), nullable=False),
        sa.Column('user_type', sa.Enum('Team_Member', 'Ambassador', 
                                       name='user_type'), nullable=False),
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
    
    # 2. Create tasks table (SQLAlchemy automatically creates assigned_group ENUM here)
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('assigned_to_group', sa.Enum('Team_Members', 'Ambassadors', 'All', 
                                               name='assigned_group'), nullable=False),
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
    
    # 3. Create task_assignments table
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
    op.execute("DROP TYPE IF EXISTS assigned_group CASCADE")
    op.execute("DROP TYPE IF EXISTS user_type CASCADE")
    op.execute("DROP TYPE IF EXISTS user_role CASCADE")
    