"""Forecast per site; household settings (data-source switches).

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "forecast",
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("raw", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["site_id"], ["site.id"], name=op.f("fk_forecast_site_id_site"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("site_id", name=op.f("pk_forecast")),
    )
    with op.batch_alter_table("household", schema=None) as batch_op:
        batch_op.add_column(sa.Column("settings", sa.JSON(), server_default="{}", nullable=False))


def downgrade() -> None:
    with op.batch_alter_table("household", schema=None) as batch_op:
        batch_op.drop_column("settings")
    op.drop_table("forecast")
