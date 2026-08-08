"""Add deleted_at to campaigns for soft-delete support.

Mirrors 011_quest_soft_delete.py. Soft rather than hard delete because campaign
completions have already credited PP through the immutable PointsTransaction
ledger — a hard delete would cascade those rows away and orphan the audit trail.

Revision ID: d7e8f9a0b1c2
Revises: c6d7e8f9a0b1
Create Date: 2026-08-08
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d7e8f9a0b1c2"
down_revision = "c6d7e8f9a0b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("campaigns", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_campaigns_deleted_at", "campaigns", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_campaigns_deleted_at", table_name="campaigns")
    op.drop_column("campaigns", "deleted_at")
