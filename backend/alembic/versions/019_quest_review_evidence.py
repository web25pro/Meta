"""Store quest review evidence and decisions."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a0b1c2d3e4f5"
down_revision = "f9a0b1c2d3e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("quest_completions", sa.Column("reviewed_by_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("quest_completions", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("quest_completions", sa.Column("review_reason", sa.String(500), nullable=True))
    op.create_foreign_key(
        "fk_quest_completions_reviewed_by", "quest_completions", "users",
        ["reviewed_by_id"], ["id"], ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_quest_completions_reviewed_by", "quest_completions", type_="foreignkey")
    op.drop_column("quest_completions", "review_reason")
    op.drop_column("quest_completions", "reviewed_at")
    op.drop_column("quest_completions", "reviewed_by_id")
