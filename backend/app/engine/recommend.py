"""What to plant now or soon: turns a crop's sowing windows into dates from today. Pure."""

from __future__ import annotations

from datetime import date, timedelta


def _next(md: str, today: date) -> date:
    """The next date on or after today that falls on "MM-DD"."""
    m, d = (int(x) for x in md.split("-"))
    try:
        out = date(today.year, m, d)
    except ValueError:  # 29 February in a common year
        out = date(today.year, m, 28)
    return out if out >= today else out.replace(year=today.year + 1, day=min(d, 28) if m == 2 else d)


def timing(window: dict, today: date, horizon: int) -> dict | None:
    """Where `today` stands against one sowing window: "now" (inside it) or "soon" (it opens within `horizon` days).
    Gives the dates of the window and of its best part; None when it is not yet near."""
    if window["all_year"]:
        return {
            "state": "now",
            "start": today,
            "until": today + timedelta(days=365),
            "best_from": today,
            "best_to": today + timedelta(days=365),
            "all_year": True,
        }
    start, end = _next(window["start"], today), _next(window["end"], today)
    if end < start:  # the window began before today and has not ended
        begins = start - timedelta(days=365)
        inside = begins <= today
        state, first = ("now", today) if inside else ("soon", start)
    elif start == today:
        state, first = "now", today
    else:
        state, first = "soon", start
    if state == "soon" and (first - today).days > horizon:
        return None
    best_to = _next(window["best_end"], first)
    best_from = max(
        first, _next(window["best_start"], first) if _next(window["best_start"], first) <= best_to else first
    )
    return {"state": state, "start": first, "until": end, "best_from": best_from, "best_to": best_to, "all_year": False}


def options(analysis: dict, today: date, horizon: int) -> list[dict]:
    """Every way to start this crop that is open now or soon: direct sowing, and setting out seedlings."""
    out = []
    for method, part in (("direct", analysis), ("transplant", analysis.get("transplant"))):
        if not part or part["verdict"]["state"] != "yes":
            continue
        for w in part["windows"]:
            t = timing(w, today, horizon)
            if t:
                out.append(
                    t
                    | {
                        "method": method,
                        "age_days": part.get("age_days", 0),
                        "success": w["success"],
                        "days_to_maturity": w["days_to_maturity"],
                    }
                )
    return out


def best_option(opts: list[dict]) -> dict | None:
    """One way to start the crop: what is open now beats what is coming, then the likelier to succeed, then direct."""
    return min(
        opts,
        key=lambda o: (
            o["state"] != "now",
            o["start"] if o["state"] == "soon" else date.min,
            -o["success"],
            o["method"] != "direct",
        ),
        default=None,
    )
