"""Background jobs in the single uvicorn worker: register with @job, run by run_forever() from the app lifespan.

Jobs are plain sync functions run in a thread, so they can use the same DB sessions and httpx calls as the API.
Their last run and last error are reported in /api/health.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import now

log = logging.getLogger("cropstack.scheduler")
TICK_SECONDS = 60
FIRST_RUN_DELAY = timedelta(seconds=60)  # let start-up and the first page load finish first


@dataclass
class Job:
    name: str
    every: timedelta
    fn: Callable[[], None]
    next_run: datetime | None = None
    last_run: datetime | None = None
    last_ok: datetime | None = None
    last_error: str | None = None


JOBS: dict[str, Job] = {}


def job(name: str, every: timedelta) -> Callable[[Callable[[], None]], Callable[[], None]]:
    def register(fn: Callable[[], None]) -> Callable[[], None]:
        JOBS[name] = Job(name, every, fn)
        return fn

    return register


def run_due(at: datetime) -> list[str]:
    """Run every job that is due (blocking). Returns the names that ran. Errors are recorded, never raised."""
    ran = []
    for j in JOBS.values():
        if j.next_run is None:
            j.next_run = at + FIRST_RUN_DELAY
        if at < j.next_run:
            continue
        j.last_run, j.next_run = at, at + j.every
        try:
            j.fn()
            j.last_ok, j.last_error = now(), None
        except Exception as e:  # a failing job must never stop the others or the app
            j.last_error = f"{e.__class__.__name__}: {e}"
            log.exception("job %s failed", j.name)
        ran.append(j.name)
    return ran


async def run_forever() -> None:
    while True:
        await asyncio.to_thread(run_due, now())
        await asyncio.sleep(TICK_SECONDS)


def status() -> dict[str, dict]:
    iso = lambda d: d.isoformat() if d else None  # noqa: E731
    return {
        j.name: {"every_minutes": j.every.total_seconds() / 60, "last_run": iso(j.last_run), "last_ok": iso(j.last_ok)}
        | {"last_error": j.last_error}
        for j in JOBS.values()
    }
