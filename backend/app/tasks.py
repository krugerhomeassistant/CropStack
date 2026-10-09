"""The task engine core (SPEC §9.2): generators turn plantings into tasks, and `sync` makes the stored tasks match.

A generator is a pure function from a planting (and what the climate says about it) to `TaskSpec`s with stable keys,
so running it again updates tasks instead of duplicating them. Tasks that are done, skipped or locked are not moved.
shortcut: one generator (the crop schedule: sow, set out, first harvest) and English text; care, water and weather
alerts arrive with the engines they need (PLAN 6.4-6.7), and generated text moves into the i18n layer with Today.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from sqlmodel import Session, select

from .models import Planting, Task, TaskChange, now

Maturity = dict[str, int]  # p10 / p50 / p90 days from sowing to harvest
SOW_SLACK = (3, 7)  # days a job may be done before and after its ideal day


@dataclass(frozen=True)
class TaskSpec:
    key: str
    kind: str
    group: str
    title: str
    reason: str
    earliest: date
    ideal: date
    latest: date
    done: bool = False  # the planting has already moved past this job


def _around(ideal: date) -> tuple[date, date, date]:
    return ideal - timedelta(days=SOW_SLACK[0]), ideal, ideal + timedelta(days=SOW_SLACK[1])


def _day(d: date) -> str:
    return f"{d.day} {d.strftime('%B')}"


def crop_schedule(
    p: Planting, name: str, maturity: Maturity | None, cycle_days: tuple[int, int] | None
) -> list[TaskSpec]:
    """Sow, set out (transplants) and first harvest for one planting."""
    if p.status == "failed":
        return []
    where = f" in {p.location}" if p.location else ""
    transplant = p.method == "transplant"
    past = {"planned": 0, "sown": 1, "germinated": 2, "transplanted": 3, "harvesting": 4, "finished": 5}[p.status]
    specs = [
        TaskSpec(
            f"planting:{p.id}:sow",
            "sow",
            "Plant",
            f"Sow {name} ({p.quantity}){' indoors' if transplant else where}",
            f"You planned to sow on {_day(p.start_date)}.",
            *_around(p.start_date),
            done=past >= 1,
        )
    ]
    if transplant and p.set_out_date:
        specs.append(
            TaskSpec(
                f"planting:{p.id}:set_out",
                "set_out",
                "Plant",
                f"Set out {name} seedlings ({p.quantity}){where}",
                f"The seedlings sown indoors on {_day(p.start_date)} are ready to go out on {_day(p.set_out_date)}.",
                *_around(p.set_out_date),
                done=past >= 3,
            )
        )
    if maturity:
        low, mid, high = (p.start_date + timedelta(days=maturity[q]) for q in ("p10", "p50", "p90"))
        reason = (
            f"Sown on {_day(p.start_date)}, {name} usually ripens after about {maturity['p50']} days "
            f"(most years {maturity['p10']} to {maturity['p90']}), worked out from its heat needs and your climate."
        )
    elif cycle_days:
        low, mid, high = (
            p.start_date + timedelta(days=d) for d in (cycle_days[0], sum(cycle_days) // 2, cycle_days[1])
        )
        reason = f"{name} usually takes {cycle_days[0]} to {cycle_days[1]} days from sowing to harvest."
    else:
        return specs
    specs.append(
        TaskSpec(
            f"planting:{p.id}:harvest",
            "harvest",
            "Harvest",
            f"Start harvesting {name}{where}",
            reason,
            low,
            mid,
            high,
            done=past >= 4,
        )
    )
    return specs


def sync(db: Session, household_id: int, make_specs: Callable[[Planting], list[TaskSpec]]) -> None:
    """Make the household's open tasks match what the generators now say. Caller commits."""
    existing = {t.generator_key: t for t in db.exec(select(Task).where(Task.household_id == household_id))}
    plantings = db.exec(select(Planting).where(Planting.household_id == household_id)).all()
    wanted: dict[str, tuple[Planting, TaskSpec]] = {s.key: (p, s) for p in plantings for s in make_specs(p)}

    def log(task: Task, what: str) -> None:
        db.add(TaskChange(task_id=task.id, what=what))

    for key, (planting, spec) in wanted.items():
        task = existing.get(key)
        if task is None:
            if not spec.done:
                db.add(
                    Task(
                        household_id=household_id,
                        generator_key=key,
                        planting_id=planting.id,
                        kind=spec.kind,
                        group=spec.group,
                        title=spec.title,
                        reason=spec.reason,
                        earliest=spec.earliest,
                        ideal=spec.ideal,
                        latest=spec.latest,
                    )
                )
            continue
        if task.status != "open":
            continue
        if spec.done:
            task.status, task.completed_at = "done", now()
            log(task, "Done: the planting has moved on")
        elif task.locked:
            continue
        elif (task.title, task.reason, task.earliest, task.ideal, task.latest) != (
            spec.title,
            spec.reason,
            spec.earliest,
            spec.ideal,
            spec.latest,
        ):
            if task.ideal != spec.ideal:
                log(task, f"Moved from {_day(task.ideal)} to {_day(spec.ideal)}")
            task.title, task.reason = spec.title, spec.reason
            task.earliest, task.ideal, task.latest = spec.earliest, spec.ideal, spec.latest
        db.add(task)
    for key, task in existing.items():
        if key not in wanted and task.status == "open":
            task.status = "skipped"
            db.add(task)
            log(task, "Skipped: nothing needs this any more")
