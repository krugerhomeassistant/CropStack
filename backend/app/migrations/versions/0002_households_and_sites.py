"""Households, memberships, invites; garden becomes a household's site.

Data: every existing user becomes the owner of their own household (household.id = user.id), and their
garden becomes that household's site (same id). The climate cache is rebuilt empty: it is refetched on
the next visit, which is simpler and safer than moving its key.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

AutoString = sqlmodel.sql.sqltypes.AutoString
UTCDateTime = sqlmodel.sql.sqltypes.UTCDateTime


def upgrade() -> None:
    op.create_table(
        "household",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", AutoString(), nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_household")),
    )
    op.create_table(
        "membership",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("role", AutoString(), nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["household_id"], ["household.id"], name=op.f("fk_membership_household_id_household"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_membership_user_id_user"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_membership")),
    )
    op.create_index(op.f("ix_membership_household_id"), "membership", ["household_id"], unique=False)
    op.create_table(
        "invite",
        sa.Column("token_hash", AutoString(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("role", AutoString(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.Column("expires_at", UTCDateTime(), nullable=False),
        sa.Column("used_at", UTCDateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"], ["user.id"], name=op.f("fk_invite_created_by_user"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["household_id"], ["household.id"], name=op.f("fk_invite_household_id_household"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("token_hash", name=op.f("pk_invite")),
    )
    op.create_index(op.f("ix_invite_household_id"), "invite", ["household_id"], unique=False)
    op.create_table(
        "site",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("name", AutoString(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("postal_code", AutoString(), nullable=False),
        sa.Column("frost_probability", sa.Integer(), nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.Column("updated_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["household_id"], ["household.id"], name=op.f("fk_site_household_id_household"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_site")),
        sa.UniqueConstraint("household_id", name=op.f("uq_site_household_id")),
    )

    # Move the data: one household per existing user, owned by them; their garden becomes its site.
    op.execute(
        "INSERT INTO household (id, name, created_at) "
        "SELECT id, COALESCE(NULLIF(display_name, ''), username) || '''s homestead', created_at FROM user"
    )
    op.execute(
        "INSERT INTO membership (user_id, household_id, role, created_at) SELECT id, id, 'owner', created_at FROM user"
    )
    op.execute(
        "INSERT INTO site (id, household_id, name, latitude, longitude, postal_code, frost_probability,"
        " created_at, updated_at) "
        "SELECT id, user_id, name, latitude, longitude, postal_code, frost_probability, created_at, updated_at"
        " FROM garden"
    )

    op.drop_table("climatecache")
    op.drop_table("garden")
    op.create_table(
        "climatecache",
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("fetched_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["site_id"], ["site.id"], name=op.f("fk_climatecache_site_id_site"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("site_id", name=op.f("pk_climatecache")),
    )


def downgrade() -> None:
    raise NotImplementedError("Restore a backup to go back before households (0002).")
