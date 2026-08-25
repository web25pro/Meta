"""add wallet and tier columns to users

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7
Create Date: 2026-08-25 16:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a8'
down_revision = 'a1b2c3d4e5f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Wallet & membership tier columns (LPanda Premium)
    op.add_column('users', sa.Column('wallet_address', sa.String(42), nullable=True))
    op.create_index('ix_users_wallet_address', 'users', ['wallet_address'])
    op.add_column('users', sa.Column('wallet_verified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('membership_tier', sa.String(16), nullable=False, server_default='standard'))
    op.add_column('users', sa.Column('tier_updated_at', sa.DateTime(timezone=True), nullable=True))

    # Transitional PP balance buckets
    op.add_column('users', sa.Column('available_points', sa.Numeric(18, 2), nullable=True))
    op.add_column('users', sa.Column('locked_points', sa.Numeric(18, 2), nullable=True))
    op.add_column('users', sa.Column('escrow_points', sa.Numeric(18, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'escrow_points')
    op.drop_column('users', 'locked_points')
    op.drop_column('users', 'available_points')
    op.drop_column('users', 'tier_updated_at')
    op.drop_column('users', 'membership_tier')
    op.drop_column('users', 'wallet_verified_at')
    op.drop_index('ix_users_wallet_address', table_name='users')
    op.drop_column('users', 'wallet_address')
