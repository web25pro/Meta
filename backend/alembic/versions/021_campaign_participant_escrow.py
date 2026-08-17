"""Add per-participant campaign reward escrow."""

from alembic import op
import sqlalchemy as sa


revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "campaign_participations",
        sa.Column("pp_earned", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "campaign_participations",
        sa.Column("pp_withdrawn", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )
    op.alter_column("campaign_participations", "pp_earned", server_default=None)
    op.alter_column("campaign_participations", "pp_withdrawn", server_default=None)


def downgrade() -> None:
    op.drop_column("campaign_participations", "pp_withdrawn")
    op.drop_column("campaign_participations", "pp_earned")
