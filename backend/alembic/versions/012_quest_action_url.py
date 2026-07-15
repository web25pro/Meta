"""Add action_url column to quests for clickable quest links.

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-07-15
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f3a4b5c6d7e8"
down_revision = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("quests", sa.Column("action_url", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("quests", "action_url")
