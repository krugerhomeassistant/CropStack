"""The task engine core (SPEC §9.2): generators turn plantings into tasks, and `sync` makes the stored tasks match.

A generator is a pure function from a planting (and what the climate says about it) to `TaskSpec`s with stable keys,
so running it again updates tasks instead of duplicating them. Tasks that are done, skipped or locked are not moved.
shortcut: two generators (the crop schedule, and frost/heat protection from the forecast) and English text with
temperatures in °C; care and water jobs arrive with the engines they need (PLAN 6.4-6.7), and generated text and
units move into the i18n layer with Today.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from sqlmodel import Session, select

from .engine import water
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


EXPOSED = ("sown", "germinated", "transplanted", "harvesting")


def weather_alerts(
    p: Planting,
    name: str,
    lethal_min: float | None,
    stress_max: float | None,
    forecast: list[dict],
    horizon: int = 7,
) -> list[TaskSpec]:
    """Protect jobs for a planting that is outdoors: the first forecast night at or below its killing temperature,
    and the first day at or above the temperature where it stops growing. `forecast` = daily rows from today on."""
    outdoors = p.status in EXPOSED and not (p.method == "transplant" and p.status in ("sown", "germinated"))
    if not outdoors:
        return []
    where = f" in {p.location}" if p.location else ""
    specs = []
    days = [r for r in forecast[:horizon] if r.get("tmin") is not None and r.get("tmax") is not None]
    for kind, title, hit, text in (
        (
            "frost",
            "Cover {name}{where} against frost",
            lambda r: lethal_min is not None and r["tmin"] <= lethal_min,
            lambda r: (
                f"A night of {r['tmin']:.0f} °C is forecast for {_day(date.fromisoformat(r['date']))}; {name} is damaged at {lethal_min:.0f} °C or below. Cover it that evening."
            ),
        ),
        (
            "heat",
            "Shade and water {name}{where} in the heat",
            lambda r: stress_max is not None and r["tmax"] >= stress_max,
            lambda r: (
                f"A high of {r['tmax']:.0f} °C is forecast for {_day(date.fromisoformat(r['date']))}; {name} stops growing above {stress_max:.0f} °C. Water well and give it shade."
            ),
        ),
    ):
        first = next((r for r in days if hit(r)), None)
        if first:
            day = date.fromisoformat(first["date"])
            specs.append(
                TaskSpec(
                    f"planting:{p.id}:{kind}",
                    kind,
                    "Protect",
                    title.format(name=name, where=where),
                    text(first),
                    day - timedelta(days=2),
                    day - timedelta(days=1),
                    day,
                )
            )
    return specs


def water_alerts(
    p: Planting, name: str, profile: water.WaterProfile, last_watered: date | None, rows: list[dict], today: date
) -> list[TaskSpec]:
    """A Water job when the soil around an outdoor planting is expected to pass its dry point in the next 3 days.
    `rows` = daily weather (observed and forecast); the soil counts as full at sowing, at set-out, or when the
    household last said it watered, whichever is latest. The key includes that date, so each watering starts afresh."""
    if p.status not in EXPOSED or (p.method == "transplant" and p.status in ("sown", "germinated")):
        return []
    wet_since = max(d for d in (p.set_out_date if p.method == "transplant" else None, p.start_date, last_watered) if d)
    path = water.depletion_path(profile, p.start_date, wet_since, rows)
    dry = water.first_dry_day(path, today)
    if not dry:
        return []
    since = (
        "the last watering"
        if wet_since == last_watered
        else "it was set out"
        if wet_since == p.set_out_date and p.method == "transplant"
        else "sowing"
    )
    mm = round(dry["depletion"])
    where = f" in {p.location}" if p.location else ""
    day = max(dry["date"], today)
    return [
        TaskSpec(
            f"planting:{p.id}:water:{last_watered or 'start'}",
            "water",
            "Water",
            f"Water {name}{where}",
            f"The soil is expected to be dry by {_day(dry['date'])}: about {mm} mm of water used since {since} on "
            f"{_day(wet_since)}, less the rain. Give about {mm} mm, which is {mm} litres for every square metre.",
            max(wet_since, day - timedelta(days=1)),
            day,
            day + timedelta(days=2),
        )
    ]


def sync(db: Session, household_id: int, make_specs: Callable[[Planting], list[TaskSpec]], kinds: set[str]) -> None:
    """Make the household's tasks of these kinds match what the generator now says. Caller commits."""
    existing = {
        t.generator_key: t
        for t in db.exec(select(Task).where(Task.household_id == household_id, Task.kind.in_(kinds)))  # type: ignore[attr-defined]
    }
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
        if task.status == "skipped" and task.completed_by is None and not spec.done:
            task.status, task.completed_at = "open", None  # skipped by the engine, not a person: needed again
            log(task, "Reopened: needed again")
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
