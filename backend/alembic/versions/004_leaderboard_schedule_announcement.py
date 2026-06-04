"""Add leaderboard, schedule, and announcement models

Revision ID: 004
Revises: 003
Create Date: 2024-01-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create leaderboard_cache table
    op.create_table(
        'leaderboard_cache',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('user_type', sa.String(50), nullable=False),
        sa.Column('rank', sa.Integer, nullable=False),
        sa.Column('total_pp', sa.Numeric(10, 2), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for leaderboard_cache table
    op.create_index('ix_leaderboard_cache_id', 'leaderboard_cache', ['id'])
    op.create_index('ix_leaderboard_cache_user_id', 'leaderboard_cache', ['user_id'])
    op.create_index('ix_leaderboard_cache_user_type', 'leaderboard_cache', ['user_type'])
    op.create_index('ix_leaderboard_cache_rank', 'leaderboard_cache', ['rank'])
    op.create_index('ix_leaderboard_cache_total_pp', 'leaderboard_cache', ['total_pp'])
    
    # Create schedules table
    op.create_table(
        'schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('event_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('target_group', sa.Enum('Team_Members', 'Ambassadors', 'All',
                                          name='target_group', create_type=True), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for schedules table
    op.create_index('ix_schedules_id', 'schedules', ['id'])
    op.create_index('ix_schedules_event_date', 'schedules', ['event_date'])
    op.create_index('ix_schedules_target_group', 'schedules', ['target_group'])
    op.create_index('ix_schedules_created_by_id', 'schedules', ['created_by_id'])
    
    # Create announcements table
    op.create_table(
        'announcements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('target_group', sa.Enum('Team_Members', 'Ambassadors', 'All',
                                          name='target_group', create_type=False), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for announcements table
    op.create_index('ix_announcements_id', 'announcements', ['id'])
    op.create_index('ix_announcements_target_group', 'announcements', ['target_group'])
    op.create_index('ix_announcements_created_by_id', 'announcements', ['created_by_id'])
    op.create_index('ix_announcements_created_at', 'announcements', ['created_at'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('announcements')
    op.drop_table('schedules')
    op.drop_table('leaderboard_cache')
