"""plantings remember when the year plan made them

Revision ID: 0016
Revises: 0015
Create Date: 2026-10-11

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | Sequence[str] | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("planting", sa.Column("source", sa.String(), nullable=False, server_default=""))
    # Plans accepted before this column existed: still-to-do plantings saved in one go (5 or more in the same second
    # by the same person) were made by the year plan, so "Clear plan" can find them.
    op.execute(
        """UPDATE planting SET source = 'plan' WHERE status = 'planned' AND bed_id IS NOT NULL AND EXISTS (
             SELECT 1 FROM planting o WHERE o.household_id = planting.household_id
               AND o.created_by IS planting.created_by AND substr(o.created_at, 1, 19) = substr(planting.created_at, 1, 19)
             GROUP BY substr(o.created_at, 1, 19) HAVING count(*) >= 5)"""
    )


def downgrade() -> None:
    op.drop_column("planting", "source")
