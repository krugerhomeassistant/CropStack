"""Alembic environment: migrates the app database (SQLite, batch mode for ALTER support)."""

from alembic import context
from sqlmodel import SQLModel

from app import models  # noqa: F401  registers the tables on SQLModel.metadata
from app.db import get_engine

config = context.config


def run_migrations() -> None:
    # The app passes its open connection (init_db); the CLI opens one from the app settings.
    connection = config.attributes.get("connection")
    if connection is not None:
        _run(connection)
        return
    with get_engine().begin() as conn:
        _run(conn)


def _run(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=SQLModel.metadata,
        render_as_batch=True,  # SQLite can't ALTER most things; batch mode recreates the table
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    raise SystemExit("Offline (SQL script) migrations are not supported.")
run_migrations()
