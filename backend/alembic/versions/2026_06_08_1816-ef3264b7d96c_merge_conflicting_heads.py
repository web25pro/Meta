"""merge conflicting heads

Revision ID: ef3264b7d96c
Revises: c3d4e5f6a7b8, c9daebf7a8b9
Create Date: 2026-06-08 18:16:51.408472

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ef3264b7d96c'
down_revision = ('c3d4e5f6a7b8', 'c9daebf7a8b9')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
