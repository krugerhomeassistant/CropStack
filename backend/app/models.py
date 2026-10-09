"""Database tables."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

# Named constraints let Alembic batch mode drop/alter them later on SQLite.
SQLModel.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def now() -> datetime:
    return datetime.now(UTC)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)  # stored lowercased
    password_hash: str
    display_name: str = ""
    created_at: datetime = Field(default_factory=now)
    # Personal settings (start screen, units); validated by routers.auth.Prefs, defaults filled on read.
    prefs: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False, server_default="{}"))


ROLES = ("owner", "member", "viewer")  # owner: everything · member: plan, log, do tasks · viewer: read-only


class Household(SQLModel, table=True):
    """The people who share a homestead: its sites, crops, animals and records."""

    id: int | None = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=now)


class Membership(SQLModel, table=True):
    # shortcut: one household per user (user_id is the key); make it a (user, household) pair when someone
    # needs to belong to two households.
    user_id: int = Field(foreign_key="user.id", primary_key=True, ondelete="CASCADE")
    household_id: int = Field(foreign_key="household.id", index=True, ondelete="CASCADE")
    role: str  # one of ROLES
    created_at: datetime = Field(default_factory=now)


class Invite(SQLModel, table=True):
    """A one-time link to join a household; only a SHA-256 hash of the token is stored."""

    token_hash: str = Field(primary_key=True)
    household_id: int = Field(foreign_key="household.id", index=True, ondelete="CASCADE")
    role: str
    created_by: int | None = Field(default=None, foreign_key="user.id", ondelete="SET NULL")
    created_at: datetime = Field(default_factory=now)
    expires_at: datetime
    used_at: datetime | None = None


class Site(SQLModel, table=True):
    """A place where the household grows or keeps animals; its location drives every climate calculation."""

    id: int | None = Field(default=None, primary_key=True)
    # shortcut: one site per household (unique) until the multi-site UI exists (SPEC 4.1).
    household_id: int = Field(foreign_key="household.id", unique=True, ondelete="CASCADE")
    name: str = "My garden"
    latitude: float
    longitude: float
    postal_code: str = ""
    # Risk accepted for frost dates: 50 = median date (half of years still frost after the spring date).
    frost_probability: int = 50
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)


class ClimateArchive(SQLModel, table=True):
    """A site's raw daily weather record (Open-Meteo archive response): the input of every climate question.

    Refetched when the site moves, when a newer complete year exists, or when `version` changes."""

    site_id: int = Field(foreign_key="site.id", primary_key=True, ondelete="CASCADE")
    latitude: float
    longitude: float
    version: int
    last_year: int  # last complete year in the record
    raw: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    fetched_at: datetime = Field(default_factory=now)
