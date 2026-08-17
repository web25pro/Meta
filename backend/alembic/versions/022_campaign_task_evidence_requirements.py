"""Add configurable campaign task evidence requirements."""

from alembic import op
import sqlalchemy as sa


revision = "d3e4f5a6b7c8"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "campaign_tasks",
        sa.Column("screenshot_required", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "campaign_tasks",
        sa.Column("link_required", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("campaign_tasks", "screenshot_required", server_default=None)
    op.alter_column("campaign_tasks", "link_required", server_default=None)


def downgrade() -> None:
    op.drop_column("campaign_tasks", "link_required")
    op.drop_column("campaign_tasks", "screenshot_required")
