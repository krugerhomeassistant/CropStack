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


class Garden(SQLModel, table=True):
    """A user's growing site; its location drives every climate calculation."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, ondelete="CASCADE")  # one garden per user for now
    name: str = "My garden"
    latitude: float
    longitude: float
    postal_code: str = ""
    # Risk accepted for frost dates: 50 = median date (half of years still frost after the spring date).
    frost_probability: int = 50
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)


class ClimateCache(SQLModel, table=True):
    """Condensed climate record for a garden's location (see climate.summarize); refetched when it moves."""

    garden_id: int = Field(foreign_key="garden.id", primary_key=True, ondelete="CASCADE")
    latitude: float
    longitude: float
    summary: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    fetched_at: datetime = Field(default_factory=now)
