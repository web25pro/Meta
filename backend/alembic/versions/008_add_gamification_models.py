"""Add gamification models

Revision ID: 008
Revises: 007
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c9daebf7a8b9'
down_revision = 'b8c9daebf7a8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add gamification tables"""
    # Create enum types
    op.execute("CREATE TYPE badge_type AS ENUM ('Task_Based', 'Points_Based', 'Streak_Based', 'Special')")
    op.execute("CREATE TYPE badge_rarity AS ENUM ('Common', 'Rare', 'Epic', 'Legendary')")
    op.execute("CREATE TYPE leaderboard_period AS ENUM ('All_Time', 'Monthly', 'Weekly')")
    op.execute("CREATE TYPE theme_mode AS ENUM ('Dark', 'Light')")
    op.execute("CREATE TYPE font_size AS ENUM ('Small', 'Medium', 'Large')")
    op.execute("CREATE TYPE abuse_type AS ENUM ('Referral_Spam', 'Multi_Account', 'Bot_Activity', 'Suspicious_Pattern')")
    op.execute("CREATE TYPE abuse_severity AS ENUM ('Low', 'Medium', 'High', 'Critical')")
    
    # Create game_rewards table
    op.create_table(
        'game_rewards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('game_name', sa.String(255), nullable=False),
        sa.Column('tournament_name', sa.String(255), nullable=False),
        sa.Column('winner_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reward_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('placement', sa.Integer(), nullable=False),
        sa.Column('is_claimed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('claimed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_data', postgresql.JSON(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('reward_amount > 0', name='check_reward_amount_positive'),
        sa.CheckConstraint('placement > 0', name='check_placement_positive')
    )
    op.create_index('ix_game_rewards_id', 'game_rewards', ['id'])
    op.create_index('ix_game_rewards_game_id', 'game_rewards', ['game_id'])
    op.create_index('ix_game_rewards_winner_user_id', 'game_rewards', ['winner_user_id'])
    op.create_index('ix_game_rewards_is_claimed', 'game_rewards', ['is_claimed'])
    op.create_index('ix_game_rewards_expires_at', 'game_rewards', ['expires_at'])
    
    # Create badges table
    op.create_table(
        'badges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('icon_url', sa.String(500), nullable=False),
        sa.Column('badge_type', postgresql.ENUM('Task_Based', 'Points_Based', 'Streak_Based', 'Special', name='badge_type', create_type=False), nullable=False),
        sa.Column('criteria', postgresql.JSON(), nullable=False),
        sa.Column('rarity', postgresql.ENUM('Common', 'Rare', 'Epic', 'Legendary', name='badge_rarity', create_type=False), nullable=False),
        sa.Column('points_reward', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'))
    )
    op.create_index('ix_badges_id', 'badges', ['id'])
    op.create_index('ix_badges_badge_type', 'badges', ['badge_type'])
    op.create_index('ix_badges_rarity', 'badges', ['rarity'])
    
    # Create user_badges table
    op.create_table(
        'user_badges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('badge_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('badges.id', ondelete='CASCADE'), nullable=False),
        sa.Column('earned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('progress', sa.Numeric(3, 2), nullable=False, server_default='0.0'),
        sa.UniqueConstraint('user_id', 'badge_id', name='uq_user_badge'),
        sa.CheckConstraint('progress >= 0.0 AND progress <= 1.0', name='check_progress_range')
    )
    op.create_index('ix_user_badges_id', 'user_badges', ['id'])
    op.create_index('ix_user_badges_user_id', 'user_badges', ['user_id'])
    op.create_index('ix_user_badges_badge_id', 'user_badges', ['badge_id'])
    
    # Create referrals table
    op.create_table(
        'referrals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('referrer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('referee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('referral_code', sa.String(8), nullable=False),
        sa.Column('referrer_bonus', sa.Numeric(10, 2), nullable=False, server_default='50.0'),
        sa.Column('referee_bonus', sa.Numeric(10, 2), nullable=False, server_default='25.0'),
        sa.Column('is_bonus_awarded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('bonus_awarded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('referee_completed_first_task', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('referee_id', name='uq_referee'),
        sa.CheckConstraint('referrer_id != referee_id', name='check_no_self_referral')
    )
    op.create_index('ix_referrals_id', 'referrals', ['id'])
    op.create_index('ix_referrals_referrer_id', 'referrals', ['referrer_id'])
    op.create_index('ix_referrals_referee_id', 'referrals', ['referee_id'])
    
    # Create public_leaderboard table
    op.create_table(
        'public_leaderboard',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('time_period', postgresql.ENUM('All_Time', 'Monthly', 'Weekly', name='leaderboard_period', create_type=False), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('points_earned', sa.Numeric(10, 2), nullable=False),
        sa.Column('tasks_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('badges_earned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rank_change', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('user_id', 'time_period', name='uq_user_period')
    )
    op.create_index('ix_public_leaderboard_id', 'public_leaderboard', ['id'])
    op.create_index('ix_public_leaderboard_user_id', 'public_leaderboard', ['user_id'])
    op.create_index('ix_public_leaderboard_time_period', 'public_leaderboard', ['time_period'])
    op.create_index('ix_public_leaderboard_rank', 'public_leaderboard', ['rank'])
    
    # Create user_theme_preferences table
    op.create_table(
        'user_theme_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('theme_mode', postgresql.ENUM('Dark', 'Light', name='theme_mode', create_type=False), nullable=False, server_default='Dark'),
        sa.Column('accent_color', sa.String(7), nullable=False, server_default='#00FF88'),
        sa.Column('enable_animations', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('reduce_motion', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('font_size', postgresql.ENUM('Small', 'Medium', 'Large', name='font_size', create_type=False), nullable=False, server_default='Medium'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('user_id', name='uq_user_theme')
    )
    op.create_index('ix_user_theme_preferences_id', 'user_theme_preferences', ['id'])
    
    # Create community_analytics table
    op.create_table(
        'community_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('date', sa.Date(), nullable=False, unique=True),
        sa.Column('total_users', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('new_users', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('active_users', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tasks_submitted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tasks_approved', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_points_awarded', sa.Numeric(12, 2), nullable=False, server_default='0.0'),
        sa.Column('total_referrals', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_badges_awarded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_tasks_per_user', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('date', name='uq_analytics_date')
    )
    op.create_index('ix_community_analytics_id', 'community_analytics', ['id'])
    op.create_index('ix_community_analytics_date', 'community_analytics', ['date'])
    
    # Create abuse_detection_logs table
    op.create_table(
        'abuse_detection_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('abuse_type', postgresql.ENUM('Referral_Spam', 'Multi_Account', 'Bot_Activity', 'Suspicious_Pattern', name='abuse_type', create_type=False), nullable=False),
        sa.Column('severity', postgresql.ENUM('Low', 'Medium', 'High', 'Critical', name='abuse_severity', create_type=False), nullable=False),
        sa.Column('detection_method', sa.String(255), nullable=False),
        sa.Column('evidence', postgresql.JSON(), nullable=False),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action_taken', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'))
    )
    op.create_index('ix_abuse_detection_logs_id', 'abuse_detection_logs', ['id'])
    op.create_index('ix_abuse_detection_logs_user_id', 'abuse_detection_logs', ['user_id'])
    op.create_index('ix_abuse_detection_logs_abuse_type', 'abuse_detection_logs', ['abuse_type'])
    op.create_index('ix_abuse_detection_logs_severity', 'abuse_detection_logs', ['severity'])
    op.create_index('ix_abuse_detection_logs_is_resolved', 'abuse_detection_logs', ['is_resolved'])


def downgrade() -> None:
    """Remove gamification tables"""
    # Drop tables
    op.drop_table('abuse_detection_logs')
    op.drop_table('community_analytics')
    op.drop_table('user_theme_preferences')
    op.drop_table('public_leaderboard')
    op.drop_table('referrals')
    op.drop_table('user_badges')
    op.drop_table('badges')
    op.drop_table('game_rewards')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS abuse_severity")
    op.execute("DROP TYPE IF EXISTS abuse_type")
    op.execute("DROP TYPE IF EXISTS font_size")
    op.execute("DROP TYPE IF EXISTS theme_mode")
    op.execute("DROP TYPE IF EXISTS leaderboard_period")
    op.execute("DROP TYPE IF EXISTS badge_rarity")
    op.execute("DROP TYPE IF EXISTS badge_type")
