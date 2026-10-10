"""Database tables."""

from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import JSON, Column, Integer, String, UniqueConstraint
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
    # Household-wide switches (data sources); validated by routers.household.HouseholdSettings.
    settings: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False, server_default="{}"))
    # The garden assistant's provider, model and key (routers.ai); the key never leaves the server.
    ai: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False, server_default="{}"))


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
    soil: str = ""  # "", sandy, loamy or clay: how much water the ground holds (engine/water.py)
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


class CatalogOverride(SQLModel, table=True):
    """A household's own value for one catalog field (e.g. its tomatoes' lethal_min), winning over the catalog."""

    household_id: int = Field(foreign_key="household.id", primary_key=True, ondelete="CASCADE")
    kind: str = Field(primary_key=True)
    slug: str = Field(primary_key=True)
    path: str = Field(primary_key=True)  # dotted, e.g. requirements.temperature.lethal_min
    value: Any = Field(sa_column=Column(JSON, nullable=False))
    updated_at: datetime = Field(default_factory=now)


class Forecast(SQLModel, table=True):
    """Latest Open-Meteo forecast for a site: the past 92 days observed and the next 16 days forecast."""

    site_id: int = Field(foreign_key="site.id", primary_key=True, ondelete="CASCADE")
    latitude: float
    longitude: float
    raw: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    fetched_at: datetime = Field(default_factory=now)


class Bed(SQLModel, table=True):
    """A rectangle of growing space on the garden plan. Metres from the plan's top-left corner."""

    id: int | None = Field(default=None, primary_key=True)
    household_id: int = Field(foreign_key="household.id", ondelete="CASCADE", index=True)
    name: str
    kind: str = "bed"  # bed, container or row
    x: float = 0
    y: float = 0
    width: float  # m, along x
    length: float  # m, along y
    cell_cm: int = Field(
        default=30, sa_column=Column(Integer, nullable=False, server_default="30")
    )  # size of one square cell
    # Beds sharing a layout name move together on the plan ("Back garden"); empty = on its own.
    layout: str = Field(default="", sa_column=Column(String, nullable=False, server_default=""))
    created_at: datetime = Field(default_factory=now)


class Planting(SQLModel, table=True):
    """Something the household has planted or means to: a crop, how, when, how many, and how it is getting on."""

    id: int | None = Field(default=None, primary_key=True)
    household_id: int = Field(foreign_key="household.id", ondelete="CASCADE", index=True)
    crop: str  # catalog crop slug
    method: str  # "direct" or "transplant"
    status: str = "planned"  # planned, sown, germinated, transplanted, harvesting, finished, failed
    start_date: date  # when it is (or will be) sown: in the ground, or indoors for a transplant
    set_out_date: date | None = None  # transplants only
    quantity: int = 1
    location: str = ""  # the bed's name when it is in a bed, otherwise free text
    bed_id: int | None = Field(default=None, foreign_key="bed.id", ondelete="SET NULL", index=True)
    cells: list[list[int]] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False, server_default="[]")
    )  # [column, row] in the bed
    ends_on: date | None = None  # last day it holds its cells; blank = the crop's longest cycle after planting
    notes: str = ""
    created_by: int | None = Field(default=None, foreign_key="user.id", ondelete="SET NULL")
    created_at: datetime = Field(default_factory=now)


class Task(SQLModel, table=True):
    """A job to do, made by a generator from the household's plantings. `generator_key` makes regeneration update
    the same task instead of adding another (SPEC §9.2)."""

    __table_args__ = (UniqueConstraint("household_id", "generator_key"),)

    id: int | None = Field(default=None, primary_key=True)
    household_id: int = Field(foreign_key="household.id", ondelete="CASCADE", index=True)
    generator_key: str  # e.g. "planting:12:sow"; unique per household
    planting_id: int | None = Field(default=None, foreign_key="planting.id", ondelete="CASCADE")
    kind: str  # sow, set_out, harvest
    group: str  # the Today group: Plant, Harvest, ...
    title: str
    reason: str = ""  # why now, in plain words (every task explains itself)
    earliest: date
    ideal: date
    latest: date
    status: str = "open"  # open, done, skipped
    locked: bool = False  # the user fixed the dates; the generator warns instead of moving it
    completed_at: datetime | None = None
    completed_by: int | None = Field(default=None, foreign_key="user.id", ondelete="SET NULL")
    created_at: datetime = Field(default_factory=now)


class TaskChange(SQLModel, table=True):
    """Why a task changed: the log behind "moved 5 days later: forecast frost"."""

    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id", ondelete="CASCADE", index=True)
    at: datetime = Field(default_factory=now)
    what: str


class Harvest(SQLModel, table=True):
    """Something picked from a planting: what the garden actually yields (SPEC §10.1)."""

    id: int | None = Field(default=None, primary_key=True)
    household_id: int = Field(foreign_key="household.id", ondelete="CASCADE", index=True)
    planting_id: int = Field(foreign_key="planting.id", ondelete="CASCADE", index=True)
    harvested_on: date
    quantity: float
    unit: str  # kg, g, count or bunch
    notes: str = ""
    created_by: int | None = Field(default=None, foreign_key="user.id", ondelete="SET NULL")
    created_at: datetime = Field(default_factory=now)


class PantryItem(SQLModel, table=True):
    """Food that has been put by: jars, bags, a crate in the cellar. Why: use it before it spoils (PLAN 13)."""

    id: int | None = Field(default=None, primary_key=True)
    household_id: int = Field(foreign_key="household.id", ondelete="CASCADE", index=True)
    name: str
    method: str  # canned, frozen, dried, fermented, cellar or fresh
    crop: str = ""  # catalog slug when it came from a crop
    quantity: float
    unit: str  # jars, bags, kg, g, litres or count
    made_on: date
    best_before: date | None = None
    location: str = ""
    notes: str = ""
    created_by: int | None = Field(default=None, foreign_key="user.id", ondelete="SET NULL")
    created_at: datetime = Field(default_factory=now)
