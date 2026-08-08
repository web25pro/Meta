"""Campaign architecture — targeting, budget reservation and campaign tasks.

Adds the campaign earn loop (``campaign_tasks``, ``campaign_task_completions``),
targeting columns on ``campaigns``, and ``users.region`` as the targeting source.

Revision ID: b5c6d7e8f9a0
Revises: a4b5c6d7e8f9
Create Date: 2026-08-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b5c6d7e8f9a0"
down_revision = "a4b5c6d7e8f9"
branch_labels = None
depends_on = None


def _uuid_pk():
    return sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True)


def _ts(name, nullable=False):
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable)


def upgrade() -> None:
    # ── Targeting source ────────────────────────────────────────────────────
    op.add_column("users", sa.Column("region", sa.String(2), nullable=True))
    op.create_index("ix_users_region", "users", ["region"])

    # ── Campaign targeting, budget reservation, lifecycle ──────────────────
    op.add_column("campaigns", sa.Column("slug", sa.String(64), nullable=True))
    op.add_column("campaigns", sa.Column("pp_reserved", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("campaigns", sa.Column("max_participants", sa.Integer(), nullable=True))
    op.add_column("campaigns", sa.Column("target_regions", postgresql.JSONB(), nullable=False, server_default="[]"))
    op.add_column("campaigns", sa.Column("target_roles", postgresql.JSONB(), nullable=False, server_default="[]"))
    op.add_column("campaigns", sa.Column("min_role", sa.String(32), nullable=False, server_default="Explorer"))

    # Backfill slugs from existing titles, then enforce NOT NULL + uniqueness.
    op.execute(
        """
        UPDATE campaigns
           SET slug = left(
            regexp_replace(lower(title), '[^a-z0-9]+', '-', 'g') || '-' || left(id::text, 8),
            64
        )
        WHERE slug IS NULL
        """
    )
    op.alter_column("campaigns", "slug", nullable=False)
    op.create_unique_constraint("uq_campaigns_slug", "campaigns", ["slug"])
    op.create_index("ix_campaigns_slug", "campaigns", ["slug"])

    # Normalise any status outside the new lifecycle before constraining it.
    op.execute(
        "UPDATE campaigns SET status = 'ended' "
        "WHERE status NOT IN ('draft', 'active', 'paused', 'ended')"
    )
    op.create_check_constraint(
        "ck_campaign_status",
        "campaigns",
        "status IN ('draft', 'active', 'paused', 'ended')",
    )
    op.alter_column("campaigns", "status", server_default="draft")

    # ── Campaign tasks ─────────────────────────────────────────────────────
    op.create_table(
        "campaign_tasks",
        _uuid_pk(),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("pp_reward", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verification_type", sa.String(32), nullable=False, server_default="manual"),
        sa.Column("daily_limit", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("action_url", sa.String(512), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        _ts("created_at"),
    )
    op.create_index("ix_campaign_tasks_campaign_id", "campaign_tasks", ["campaign_id"])
    op.create_index("ix_campaign_tasks_is_active", "campaign_tasks", ["is_active"])

    op.create_table(
        "campaign_task_completions",
        _uuid_pk(),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaign_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("pp_awarded", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("proof", postgresql.JSONB(), nullable=True),
        sa.Column("reviewed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        _ts("reviewed_at", nullable=True),
        _ts("created_at"),
    )
    op.create_index("ix_campaign_task_completions_campaign_id", "campaign_task_completions", ["campaign_id"])
    op.create_index("ix_campaign_task_completions_task_id", "campaign_task_completions", ["task_id"])
    op.create_index("ix_campaign_task_completions_user_id", "campaign_task_completions", ["user_id"])
    op.create_index("ix_campaign_task_completions_status", "campaign_task_completions", ["status"])
    op.create_index("ix_campaign_task_completions_created_at", "campaign_task_completions", ["created_at"])


def downgrade() -> None:
    op.drop_table("campaign_task_completions")
    op.drop_table("campaign_tasks")

    op.drop_constraint("ck_campaign_status", "campaigns", type_="check")
    op.alter_column("campaigns", "status", server_default="active")
    op.drop_index("ix_campaigns_slug", table_name="campaigns")
    op.drop_constraint("uq_campaigns_slug", "campaigns", type_="unique")
    for col in ("min_role", "target_roles", "target_regions", "max_participants", "pp_reserved", "slug"):
        op.drop_column("campaigns", col)

    op.drop_index("ix_users_region", table_name="users")
    op.drop_column("users", "region")
