"""Add User role and type

Revision ID: 005
Revises: 004
Create Date: 2024-01-20 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'User' to user_role and user_type enums
    # Postgres doesn't allow ALTER TYPE ... ADD VALUE in a transaction
    op.execute("COMMIT")
    op.execute("ALTER TYPE user_role ADD VALUE 'User'")
    op.execute("ALTER TYPE user_type ADD VALUE 'User'")


def downgrade() -> None:
    # Removing values from an enum is not straightforward in PostgreSQL
    # Typically requires creating a new type and migrating data
    pass
