"""Baseline: the v0.4.0 schema (user, garden, climatecache).

Installs from v0.1 to v0.4 created tables with SQLModel `create_all` and have no Alembic history, and a v0.2
install has no `climatecache` yet. So each table is created only if missing: every older install converges
on this baseline without a special code path.

Revision ID: 0001
Revises:
Create Date: 2026-10-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

AutoString = sqlmodel.sql.sqltypes.AutoString
UTCDateTime = sqlmodel.sql.sqltypes.UTCDateTime


def upgrade() -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())

    if "user" not in existing:
        op.create_table(
            "user",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("username", AutoString(), nullable=False),
            sa.Column("password_hash", AutoString(), nullable=False),
            sa.Column("display_name", AutoString(), nullable=False),
            sa.Column("created_at", UTCDateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_user")),
        )
        op.create_index(op.f("ix_user_username"), "user", ["username"], unique=True)

    if "garden" not in existing:
        op.create_table(
            "garden",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("name", AutoString(), nullable=False),
            sa.Column("latitude", sa.Float(), nullable=False),
            sa.Column("longitude", sa.Float(), nullable=False),
            sa.Column("postal_code", AutoString(), nullable=False),
            sa.Column("frost_probability", sa.Integer(), nullable=False),
            sa.Column("created_at", UTCDateTime(), nullable=False),
            sa.Column("updated_at", UTCDateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_garden_user_id_user"), ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_garden")),
            sa.UniqueConstraint("user_id", name=op.f("uq_garden_user_id")),
        )

    if "climatecache" not in existing:
        op.create_table(
            "climatecache",
            sa.Column("garden_id", sa.Integer(), nullable=False),
            sa.Column("latitude", sa.Float(), nullable=False),
            sa.Column("longitude", sa.Float(), nullable=False),
            sa.Column("summary", sa.JSON(), nullable=False),
            sa.Column("fetched_at", UTCDateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["garden_id"], ["garden.id"], name=op.f("fk_climatecache_garden_id_garden"), ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("garden_id", name=op.f("pk_climatecache")),
        )


def downgrade() -> None:
    op.drop_table("climatecache")
    op.drop_table("garden")
    op.drop_index(op.f("ix_user_username"), table_name="user")
    op.drop_table("user")
