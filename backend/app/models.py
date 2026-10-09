"""Database tables."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


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
