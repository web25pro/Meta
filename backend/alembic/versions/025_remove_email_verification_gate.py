"""remove email verification gate

Revision ID: a1b2c3d4e5f7
Revises: ef3264b7d96c
Create Date: 2026-08-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f7'
down_revision = 'ef3264b7d96c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Backfill all existing users to email_verified=True
    op.execute("UPDATE users SET email_verified = true WHERE email_verified = false")

    # Change the column default to true for new users
    op.alter_column(
        'users',
        'email_verified',
        server_default=sa.text('true'),
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )


def downgrade() -> None:
    # Revert default back to false
    op.alter_column(
        'users',
        'email_verified',
        server_default=sa.text('false'),
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
    # Note: we cannot undo the backfill — users already verified stay verified.
