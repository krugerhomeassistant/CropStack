"""Schema migrations: fresh installs, upgrades from pre-Alembic releases, and model/migration drift."""

import sqlite3
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlmodel import SQLModel

from app import models  # noqa: F401  registers the tables
from app.db import init_db

V040_SCHEMA = (Path(__file__).parent / "fixtures" / "schema_v0_4_0.sql").read_text()
V020_SCHEMA = V040_SCHEMA.split("CREATE TABLE climatecache")[0]  # v0.2.0 had no climate cache
HEAD = "0009"


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "cropstack.db"


def engine_for(path):
    return create_engine(f"sqlite:///{path}")


def legacy_db(path, schema: str, with_climate: bool) -> None:
    """A database as an older release left it, with one user and garden (and cached climate)."""
    con = sqlite3.connect(path)
    con.executescript(schema)
    con.execute(
        "INSERT INTO user VALUES (1, 'kruger', 'hash', 'Kruger', '2026-10-01 10:00:00')",
    )
    con.execute(
        "INSERT INTO garden VALUES (1, 1, 'Back yard', -33.93, 18.86, '7600', 50,"
        " '2026-10-01 10:00:00', '2026-10-01 10:00:00')"
    )
    if with_climate:
        con.execute("INSERT INTO climatecache VALUES (1, -33.93, 18.86, '{\"version\": 2}', '2026-10-01 10:00:00')")
    con.commit()
    con.close()


def version(engine) -> str:
    with engine.connect() as conn:
        return conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()


def test_fresh_database_matches_models(db_path):
    engine = engine_for(db_path)
    init_db(engine)
    assert {"user", "household", "membership", "site", "climatearchive"} <= set(inspect(engine).get_table_names())
    assert version(engine) == HEAD
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), SQLModel.metadata)
    assert diff == [], f"models changed without a migration: {diff}"


@pytest.mark.parametrize(("schema", "with_climate"), [(V020_SCHEMA, False), (V040_SCHEMA, True)])
def test_upgrade_from_pre_alembic_release_keeps_data(db_path, schema, with_climate):
    legacy_db(db_path, schema, with_climate)
    engine = engine_for(db_path)
    init_db(engine)
    init_db(engine)  # idempotent on every start

    assert version(engine) == HEAD
    with engine.connect() as conn:
        assert conn.execute(text("SELECT username FROM user")).scalar_one() == "kruger"
        # The user owns a household of their own, and their garden is now its site (same id).
        assert conn.execute(text("SELECT id, name FROM household")).one() == (1, "Kruger's homestead")
        assert conn.execute(text("SELECT household_id, role FROM membership WHERE user_id = 1")).one() == (1, "owner")
        site = conn.execute(text("SELECT id, household_id, name, latitude, postal_code FROM site")).one()
        assert site == (1, 1, "Back yard", -33.93, "7600")
        assert conn.execute(text("SELECT count(*) FROM climatearchive")).scalar_one() == 0  # refetched on first visit


def test_foreign_keys_are_back_on_after_migrating(db_path):
    from app import db

    engine = db.get_engine()  # the app engine: its connect hook turns foreign keys on
    init_db(engine)
    with engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1


def test_table_rebuild_during_migration_does_not_cascade_delete(db_path, monkeypatch):
    """Batch mode rebuilds a table by copy + drop; with foreign keys on, dropping `user` deleted every garden
    (verified 2026-10-09). init_db must run migrations with foreign keys off."""
    from alembic import command
    from alembic.operations import Operations
    from sqlalchemy import Column, String

    legacy_db(db_path, V040_SCHEMA, with_climate=True)
    engine = engine_for(db_path)
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")  # as the app's connect hook leaves it

    def rebuild_user_table(cfg, _target):
        conn = cfg.attributes["connection"]
        with Operations(MigrationContext.configure(conn)).batch_alter_table("user", recreate="always") as batch:
            batch.add_column(Column("lang", String, nullable=True))

    monkeypatch.setattr(command, "upgrade", rebuild_user_table)
    init_db(engine)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM garden")).scalar_one() == 1
        assert conn.execute(text("SELECT count(*) FROM climatecache")).scalar_one() == 1
