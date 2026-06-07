"""Add public task fields

Revision ID: 007
Revises: 006
Create Date: 2024-01-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b8c9daebf7a8'
down_revision = 'a7b8c9daebf7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add public task fields to tasks table"""
    # Create new enum types
    op.execute("CREATE TYPE task_category AS ENUM ('Social_Media', 'Content_Creation', 'Community_Engagement', 'Surveys', 'Referrals')")
    op.execute("CREATE TYPE difficulty_level AS ENUM ('Easy', 'Medium', 'Hard')")
    
    # Add new columns for Public Task functionality
    # All fields are nullable or have defaults for backward compatibility
    op.add_column('tasks', sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('tasks', sa.Column('category', postgresql.ENUM('Social_Media', 'Content_Creation', 'Community_Engagement', 'Surveys', 'Referrals', name='task_category', create_type=False), nullable=True))
    op.add_column('tasks', sa.Column('max_submissions', sa.Integer(), nullable=True))
    op.add_column('tasks', sa.Column('current_submissions', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('tasks', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('tasks', sa.Column('featured', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('tasks', sa.Column('difficulty_level', postgresql.ENUM('Easy', 'Medium', 'Hard', name='difficulty_level', create_type=False), nullable=True))
    op.add_column('tasks', sa.Column('estimated_time_minutes', sa.Integer(), nullable=True))
    
    # Create indexes for performance
    op.create_index(op.f('ix_tasks_is_public'), 'tasks', ['is_public'], unique=False)
    op.create_index(op.f('ix_tasks_category'), 'tasks', ['category'], unique=False)
    op.create_index(op.f('ix_tasks_is_active'), 'tasks', ['is_active'], unique=False)


def downgrade() -> None:
    """Remove public task fields from tasks table"""
    # Drop indexes
    op.drop_index(op.f('ix_tasks_is_active'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_category'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_is_public'), table_name='tasks')
    
    # Drop columns
    op.drop_column('tasks', 'estimated_time_minutes')
    op.drop_column('tasks', 'difficulty_level')
    op.drop_column('tasks', 'featured')
    op.drop_column('tasks', 'is_active')
    op.drop_column('tasks', 'current_submissions')
    op.drop_column('tasks', 'max_submissions')
    op.drop_column('tasks', 'category')
    op.drop_column('tasks', 'is_public')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS difficulty_level")
    op.execute("DROP TYPE IF EXISTS task_category")
