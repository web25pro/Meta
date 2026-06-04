"""Add community user fields

Revision ID: 006
Revises: 005
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add community user fields to users table"""
    # Add new columns for Community User functionality
    # All fields are nullable for backward compatibility with existing users
    
    op.add_column('users', sa.Column('username', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('email_verification_token', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('email_verification_sent_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('referral_code', sa.String(length=8), nullable=True))
    op.add_column('users', sa.Column('referred_by_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('users', sa.Column('registration_ip', sa.String(length=45), nullable=True))
    op.add_column('users', sa.Column('last_login_ip', sa.String(length=45), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    
    # Add gamification fields
    op.add_column('users', sa.Column('xp', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.0'))
    op.add_column('users', sa.Column('level', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('users', sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True))
    
    # Create indexes for performance
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_referral_code'), 'users', ['referral_code'], unique=True)
    op.create_index(op.f('ix_users_referred_by_id'), 'users', ['referred_by_id'], unique=False)


def downgrade() -> None:
    """Remove community user fields from users table"""
    # Drop indexes
    op.drop_index(op.f('ix_users_referred_by_id'), table_name='users')
    op.drop_index(op.f('ix_users_referral_code'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    
    # Drop columns
    op.drop_column('users', 'last_activity_at')
    op.drop_column('users', 'current_streak')
    op.drop_column('users', 'level')
    op.drop_column('users', 'xp')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'last_login_ip')
    op.drop_column('users', 'registration_ip')
    op.drop_column('users', 'referred_by_id')
    op.drop_column('users', 'referral_code')
    op.drop_column('users', 'email_verification_sent_at')
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'username')
