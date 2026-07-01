"""Meta-Jungle ecosystem models — quests, NFTs, P2P, staking, campaigns,
learn-to-earn and marketplace redemptions.

Revision ID: d1e2f3a4b5c6
Revises: f1a2b3c4d5e6
Create Date: 2026-06-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d1e2f3a4b5c6"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def _uuid_pk():
    return sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True)


def _ts(name, nullable=False):
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable)


def upgrade() -> None:
    op.create_table(
        "quests",
        _uuid_pk(),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("pp_reward", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("category", sa.String(32), nullable=False, server_default="daily"),
        sa.Column("verification_type", sa.String(32), nullable=False, server_default="manual"),
        sa.Column("min_role", sa.String(32), nullable=False, server_default="Explorer"),
        sa.Column("steps", postgresql.JSONB(), nullable=True),
        sa.Column("daily_limit", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        _ts("starts_at", nullable=True),
        _ts("ends_at", nullable=True),
        _ts("created_at"),
    )
    op.create_index("ix_quests_category", "quests", ["category"])
    op.create_index("ix_quests_is_active", "quests", ["is_active"])

    op.create_table(
        "quest_completions",
        _uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quest_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="approved"),
        sa.Column("pp_awarded", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("proof", postgresql.JSONB(), nullable=True),
        _ts("created_at"),
    )
    op.create_index("ix_quest_completions_user_id", "quest_completions", ["user_id"])
    op.create_index("ix_quest_completions_quest_id", "quest_completions", ["quest_id"])
    op.create_index("ix_quest_completions_created_at", "quest_completions", ["created_at"])

    op.create_table(
        "nft_holdings",
        _uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contract_address", sa.String(64), nullable=False, server_default=""),
        sa.Column("token_id", sa.String(64), nullable=False, server_default=""),
        sa.Column("name", sa.String(128), nullable=False, server_default="LPanda"),
        sa.Column("tier", sa.String(16), nullable=False, server_default="common"),
        sa.Column("daily_pp_rate", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("traits", postgresql.JSONB(), nullable=True),
        sa.Column("utilities", postgresql.JSONB(), nullable=True),
        sa.Column("is_staked", sa.Boolean(), nullable=False, server_default=sa.false()),
        _ts("last_verified_at", nullable=True),
        _ts("created_at"),
    )
    op.create_index("ix_nft_holdings_user_id", "nft_holdings", ["user_id"])

    op.create_table(
        "p2p_orders",
        _uuid_pk(),
        sa.Column("seller_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("buyer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("side", sa.String(8), nullable=False, server_default="sell"),
        sa.Column("pp_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("price", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="NGN"),
        sa.Column("payment_method", sa.String(64), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("escrow_tx", sa.String(80), nullable=True),
        _ts("created_at"),
        _ts("completed_at", nullable=True),
    )
    op.create_index("ix_p2p_orders_status", "p2p_orders", ["status"])
    op.create_index("ix_p2p_orders_created_at", "p2p_orders", ["created_at"])

    op.create_table(
        "stakes",
        _uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset", sa.String(64), nullable=False, server_default="PP"),
        sa.Column("pp_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("multiplier", sa.Numeric(4, 2), nullable=False, server_default="1.0"),
        sa.Column("lock_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("accrued", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        _ts("started_at"),
        _ts("unlocked_at", nullable=True),
    )
    op.create_index("ix_stakes_user_id", "stakes", ["user_id"])
    op.create_index("ix_stakes_status", "stakes", ["status"])

    op.create_table(
        "partners",
        _uuid_pk(),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("logo_url", sa.String(512), nullable=False, server_default=""),
        sa.Column("tier", sa.String(16), nullable=False, server_default="bronze"),
        sa.Column("contact_email", sa.String(255), nullable=False, server_default=""),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        _ts("created_at"),
    )

    op.create_table(
        "campaigns",
        _uuid_pk(),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partners.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("blurb", sa.Text(), nullable=False, server_default=""),
        sa.Column("pp_budget", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pp_per_task", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pp_claimed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("total_participants", sa.Integer(), nullable=False, server_default="0"),
        _ts("starts_at", nullable=True),
        _ts("ends_at", nullable=True),
        _ts("created_at"),
    )
    op.create_index("ix_campaigns_partner_id", "campaigns", ["partner_id"])
    op.create_index("ix_campaigns_status", "campaigns", ["status"])

    op.create_table(
        "campaign_participations",
        _uuid_pk(),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        _ts("created_at"),
        sa.UniqueConstraint("campaign_id", "user_id", name="uq_campaign_participation"),
    )
    op.create_index("ix_campaign_participations_campaign_id", "campaign_participations", ["campaign_id"])
    op.create_index("ix_campaign_participations_user_id", "campaign_participations", ["user_id"])

    op.create_table(
        "courses",
        _uuid_pk(),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("blurb", sa.Text(), nullable=False, server_default=""),
        sa.Column("level", sa.String(16), nullable=False, server_default="Beginner"),
        sa.Column("lessons", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("pp_reward", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quiz", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        _ts("created_at"),
    )

    op.create_table(
        "course_completions",
        _uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("pp_awarded", sa.Numeric(10, 2), nullable=False, server_default="0"),
        _ts("created_at"),
    )
    op.create_index("ix_course_completions_user_id", "course_completions", ["user_id"])
    op.create_index("ix_course_completions_course_id", "course_completions", ["course_id"])

    op.create_table(
        "redemptions",
        _uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(64), nullable=False),
        sa.Column("product_name", sa.String(128), nullable=False),
        sa.Column("category", sa.String(32), nullable=False, server_default="airtime"),
        sa.Column("pp_cost", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("destination", sa.String(255), nullable=True),
        sa.Column("voucher_code", sa.String(64), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="completed"),
        _ts("created_at"),
    )
    op.create_index("ix_redemptions_user_id", "redemptions", ["user_id"])
    op.create_index("ix_redemptions_status", "redemptions", ["status"])
    op.create_index("ix_redemptions_created_at", "redemptions", ["created_at"])


def downgrade() -> None:
    for tbl in [
        "redemptions", "course_completions", "courses", "campaign_participations",
        "campaigns", "partners", "stakes", "p2p_orders", "nft_holdings",
        "quest_completions", "quests",
    ]:
        op.drop_table(tbl)
