"""Add Quest_Reward to transaction_type enum.

Revision ID: a4b5c6d7e8f9
Revises: f3a4b5c6d7e8
Create Date: 2026-07-15
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "a4b5c6d7e8f9"
down_revision = "f3a4b5c6d7e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'Quest_Reward'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from an enum type.
    # A full migration (create new type, migrate data, drop old) would be needed.
    pass
