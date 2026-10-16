"""seeds the household has

Revision ID: 0018
Revises: 0017
Create Date: 2026-10-16

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0018"
down_revision: str | Sequence[str] | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "seed",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("crop", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["household_id"], ["household.id"], name=op.f("fk_seed_household_id_household"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_seed")),
        sa.UniqueConstraint("household_id", "crop", name=op.f("uq_seed_household_id")),
    )
    with op.batch_alter_table("seed", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_seed_household_id"), ["household_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("seed", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_seed_household_id"))
    op.drop_table("seed")
