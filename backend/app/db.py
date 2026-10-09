"""SQLite engine (WAL, foreign keys on) and session dependency."""

from collections.abc import Iterator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, event
from sqlmodel import Session, create_engine

from .config import get_settings

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(settings.db_url, connect_args={"check_same_thread": False})

        @event.listens_for(_engine, "connect")
        def _pragmas(conn, _record) -> None:
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

    return _engine


MIGRATIONS = Path(__file__).parent / "migrations"


def init_db(engine: Engine | None = None) -> None:
    """Bring the database schema to the latest Alembic revision (runs on every start)."""
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS))
    with (engine or get_engine()).connect() as conn:
        # Batch migrations rebuild tables (copy, drop, rename); with foreign keys on, dropping a parent
        # table cascade-deletes child rows (tests/test_migrations.py). Must be set outside a transaction.
        conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
        conn.commit()  # end SQLAlchemy's autobegun transaction so begin() below starts a fresh one
        try:
            with conn.begin():
                cfg.attributes["connection"] = conn
                command.upgrade(cfg, "head")
        finally:
            conn.exec_driver_sql("PRAGMA foreign_keys=ON")  # the connection goes back to the pool
            conn.commit()


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
