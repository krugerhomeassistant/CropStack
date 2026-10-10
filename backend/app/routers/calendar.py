"""The garden calendar: sowing, setting out and harvest jobs by day."""

from datetime import date

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ..deps import MemberDep, SessionDep
from ..models import Task

router = APIRouter(prefix="/api/v1/calendar", tags=["calendar"])
KINDS = ("sow", "set_out", "harvest")  # weekly checks and watering would drown the calendar
MAX_DAYS = 100


@router.get("")
def calendar(me: MemberDep, db: SessionDep, start: date, end: date) -> list[dict]:
    """Jobs whose ideal day falls between `start` and `end`, oldest first."""
    if end < start or (end - start).days > MAX_DAYS:
        raise HTTPException(422, f"Ask for at most {MAX_DAYS} days at a time")
    rows = db.exec(
        select(Task)
        .where(
            Task.household_id == me.household_id,
            Task.kind.in_(KINDS),  # type: ignore[attr-defined]
            Task.status != "skipped",
            Task.ideal >= start,
            Task.ideal <= end,
        )
        .order_by(Task.ideal, Task.id)
    ).all()
    return [
        {"date": t.ideal, "kind": t.kind, "title": t.title, "done": t.status == "done", "planting_id": t.planting_id}
        for t in rows
    ]
