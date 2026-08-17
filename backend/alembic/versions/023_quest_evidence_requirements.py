"""Add configurable quest evidence requirements."""

from alembic import op
import sqlalchemy as sa


revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("quests", sa.Column("screenshot_required", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("quests", sa.Column("link_required", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column("quests", "screenshot_required", server_default=None)
    op.alter_column("quests", "link_required", server_default=None)


def downgrade() -> None:
    op.drop_column("quests", "link_required")
    op.drop_column("quests", "screenshot_required")
