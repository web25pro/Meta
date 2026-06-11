"""Add Community_User to user_role and user_type enums

Revision ID: f1a2b3c4d5e6
Revises: ef3264b7d96c
Create Date: 2026-06-10 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'ef3264b7d96c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'Community_User' to user_role and user_type enums
    # Postgres doesn't allow ALTER TYPE ... ADD VALUE in a transaction
    op.execute("COMMIT")
    op.execute("ALTER TYPE user_role ADD VALUE 'Community_User'")
    op.execute("ALTER TYPE user_type ADD VALUE 'Community_User'")


def downgrade() -> None:
    # Removing values from an enum is not straightforward in PostgreSQL
    pass
