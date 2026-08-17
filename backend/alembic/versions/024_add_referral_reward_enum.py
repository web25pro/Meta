"""Add Referral_Reward to the points transaction enum."""

from alembic import op


revision = "f5a6b7c8d9e0"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'Referral_Reward'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values safely.
    pass
