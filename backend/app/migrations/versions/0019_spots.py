"""plants get their own place and size in the bed

Revision ID: 0019
Revises: 0018
Create Date: 2026-10-18

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: str | Sequence[str] | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Existing plantings keep their cells; their plants are laid out from those cells the first time they are read.
    with op.batch_alter_table("planting") as batch:
        batch.add_column(sa.Column("spots", sa.JSON(), nullable=False, server_default="[]"))


def downgrade() -> None:
    with op.batch_alter_table("planting") as batch:
        batch.drop_column("spots")
