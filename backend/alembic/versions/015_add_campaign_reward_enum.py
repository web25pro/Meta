"""Add Campaign_Reward to transaction_type enum.

Split from 014 because PostgreSQL cannot use a newly added enum value in the
same transaction that adds it — see 013_add_quest_reward_enum.py.

Revision ID: c6d7e8f9a0b1
Revises: b5c6d7e8f9a0
Create Date: 2026-08-06
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "c6d7e8f9a0b1"
down_revision = "b5c6d7e8f9a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'Campaign_Reward'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from an enum type.
    # A full migration (create new type, migrate data, drop old) would be needed.
    pass
