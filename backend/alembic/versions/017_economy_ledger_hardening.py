"""Add transitional PP balance buckets and the canonical ledger."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e8f9a0b1c2d3"
down_revision = "d7e8f9a0b1c2"
branch_labels = None
depends_on = None


def _table_exists(bind, table_name: str) -> bool:
    result = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = current_schema() AND table_name = :name"
        ),
        {"name": table_name},
    )
    return result.scalar_one_or_none() is not None


def upgrade() -> None:
    op.add_column("users", sa.Column("available_points", sa.Numeric(18, 2), nullable=True))
    op.add_column("users", sa.Column("locked_points", sa.Numeric(18, 2), nullable=True))
    op.add_column("users", sa.Column("escrow_points", sa.Numeric(18, 2), nullable=True))
    op.execute("UPDATE users SET available_points = points, locked_points = 0, escrow_points = 0")

    bind = op.get_bind()
    if not _table_exists(bind, "pp_ledger_entries"):
        op.create_table(
            "pp_ledger_entries",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("amount", sa.Numeric(18, 2), nullable=False),
            sa.Column("bucket", sa.String(32), nullable=False, server_default="available"),
            sa.Column("transaction_type", sa.String(64), nullable=False),
            sa.Column("source_type", sa.String(64), nullable=True),
            sa.Column("source_id", sa.String(255), nullable=True),
            sa.Column("idempotency_key", sa.String(255), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="posted"),
            sa.Column("metadata", postgresql.JSONB(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_pp_ledger_entries_user_id", "pp_ledger_entries", ["user_id"])
        op.create_index("ix_pp_ledger_user_created", "pp_ledger_entries", ["user_id", "created_at"])
        op.create_unique_constraint("uq_pp_ledger_idempotency_key", "pp_ledger_entries", ["idempotency_key"])


def downgrade() -> None:
    op.drop_constraint("uq_pp_ledger_idempotency_key", "pp_ledger_entries", type_="unique")
    op.drop_index("ix_pp_ledger_user_created", table_name="pp_ledger_entries")
    op.drop_index("ix_pp_ledger_entries_user_id", table_name="pp_ledger_entries")
    op.drop_table("pp_ledger_entries")
    op.drop_column("users", "escrow_points")
    op.drop_column("users", "locked_points")
    op.drop_column("users", "available_points")
