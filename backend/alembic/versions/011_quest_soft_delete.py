"""Add deleted_at column to quests for soft-delete support.

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-07-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e2f3a4b5c6d7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("quests", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_quests_deleted_at", "quests", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_quests_deleted_at", table_name="quests")
    op.drop_column("quests", "deleted_at")
