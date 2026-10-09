"""Catalog overrides: a household's own values for catalog fields.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "catalogoverride",
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("kind", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("slug", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("path", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("updated_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["household.id"],
            name=op.f("fk_catalogoverride_household_id_household"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("household_id", "kind", "slug", "path", name=op.f("pk_catalogoverride")),
    )


def downgrade() -> None:
    op.drop_table("catalogoverride")
