"""add wallet and tier columns to users

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7
Create Date: 2026-08-25 16:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a8'
down_revision = 'a1b2c3d4e5f7'
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    """Check if a column exists in the given table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table)]
    return column in columns


def _index_exists(table: str, index_name: str) -> bool:
    """Check if an index exists on the given table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = [idx['name'] for idx in inspector.get_indexes(table)]
    return index_name in indexes


def upgrade() -> None:
    # Wallet & membership tier columns (LPanda Premium)
    if not _column_exists('users', 'wallet_address'):
        op.add_column('users', sa.Column('wallet_address', sa.String(42), nullable=True))
    if not _index_exists('users', 'ix_users_wallet_address'):
        op.create_index('ix_users_wallet_address', 'users', ['wallet_address'])
    if not _column_exists('users', 'wallet_verified_at'):
        op.add_column('users', sa.Column('wallet_verified_at', sa.DateTime(timezone=True), nullable=True))
    if not _column_exists('users', 'membership_tier'):
        op.add_column('users', sa.Column('membership_tier', sa.String(16), nullable=False, server_default='standard'))
    if not _column_exists('users', 'tier_updated_at'):
        op.add_column('users', sa.Column('tier_updated_at', sa.DateTime(timezone=True), nullable=True))

    # Transitional PP balance buckets
    if not _column_exists('users', 'available_points'):
        op.add_column('users', sa.Column('available_points', sa.Numeric(18, 2), nullable=True))
    if not _column_exists('users', 'locked_points'):
        op.add_column('users', sa.Column('locked_points', sa.Numeric(18, 2), nullable=True))
    if not _column_exists('users', 'escrow_points'):
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
