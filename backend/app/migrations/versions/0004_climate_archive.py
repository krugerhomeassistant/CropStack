"""Climate archive: keep each site's raw daily weather record; drop the v0.3 summary cache.

The cache held only derived numbers; the archive is refetched on the next visit (one Open-Meteo request).

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "climatearchive",
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("last_year", sa.Integer(), nullable=False),
        sa.Column("raw", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["site_id"], ["site.id"], name=op.f("fk_climatearchive_site_id_site"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("site_id", name=op.f("pk_climatearchive")),
    )
    op.drop_table("climatecache")


def downgrade() -> None:
    raise NotImplementedError("Restore a backup to go back before the climate archive (0004).")
