"""Store campaign review decisions and reasons."""
from alembic import op
import sqlalchemy as sa

revision = "b1c2d3e4f5a6"
down_revision = "a0b1c2d3e4f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("campaign_task_completions", sa.Column("review_reason", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("campaign_task_completions", "review_reason")
