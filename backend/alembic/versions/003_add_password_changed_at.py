"""Add password_changed_at field for session invalidation

Revision ID: 003
Revises: 002
Create Date: 2026-05-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add password_changed_at column to users table
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove password_changed_at column
    op.drop_column('users', 'password_changed_at')
