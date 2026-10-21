"""flocks of animals and their egg log

Revision ID: 0020
Revises: 0019
Create Date: 2026-10-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: str | Sequence[str] | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "flock",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("household_id", sa.Integer(), sa.ForeignKey("household.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("species", sa.String(), nullable=False, server_default="hen"),
        sa.Column("breed", sa.String(), nullable=False, server_default=""),
        sa.Column("count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("got_on", sa.Date(), nullable=False),
        sa.Column("coop_id", sa.Integer(), sa.ForeignKey("bed.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_flock_household_id", "flock", ["household_id"])
    op.create_table(
        "egglog",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("household_id", sa.Integer(), sa.ForeignKey("household.id", ondelete="CASCADE"), nullable=False),
        sa.Column("flock_id", sa.Integer(), sa.ForeignKey("flock.id", ondelete="CASCADE"), nullable=False),
        sa.Column("laid_on", sa.Date(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
    )
    op.create_index("ix_egglog_household_id", "egglog", ["household_id"])
    op.create_index("ix_egglog_flock_id", "egglog", ["flock_id"])


def downgrade() -> None:
    op.drop_table("egglog")
    op.drop_table("flock")
