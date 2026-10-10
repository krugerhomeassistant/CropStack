"""What a job needs to know about its own crop, read from the catalog: spacing, how long it takes to come up, soil
temperature, light. shortcut: English text and °C only, like the other generated job text."""

from __future__ import annotations


def _num(item: dict, name: str) -> float | None:
    v = item.get("params", {}).get(name)
    v = v[0] if isinstance(v, list) and v else v
    v = v.get("value") if isinstance(v, dict) else None
    return float(v) if isinstance(v, int | float) and not isinstance(v, bool) else None


def _cm(x: float) -> str:
    return f"{x:g} cm"


def _emergence(item: dict) -> str | None:
    rows = item.get("params", {}).get("days_to_emergence")
    pts = sorted(
        (r["qualifiers"]["soil_temp_c"], r["value"]) for r in rows or [] if "soil_temp_c" in r.get("qualifiers", {})
    )
    if len(pts) < 2:
        return None
    (cold_t, cold_d), (warm_t, warm_d) = pts[0], min(pts, key=lambda p: p[1])
    if cold_d == warm_d:
        return None
    return f"about {warm_d:g} days at {warm_t:g} °C soil, {cold_d:g} days if it is only {cold_t:g} °C"


def job_facts(item: dict | None, kind: str, method: str = "direct") -> list[dict]:
    """[{label, text}] for one job of this crop; empty for crops with nothing catalogued."""
    if not item:
        return []
    spread, row = _num(item, "plant_spread"), _num(item, "row_spacing")
    out: list[tuple[str, str | None]] = []
    germ = item.get("requirements", {}).get("soil_temperature", {}).get("germination", {}).get("value")
    cycle = item.get("params", {}).get("cycle_days", {}).get("value")
    sun = item.get("params", {}).get("sun", {}).get("value")
    if kind in ("sow", "set_out"):
        if spread:
            out.append(
                ("Space plants", f"{_cm(spread)} apart" + (f", rows {_cm(row)} apart" if row and row != spread else ""))
            )
        if kind == "sow" and method == "direct" and spread:
            out.append(("Thin to", f"one plant every {_cm(spread)} once the seedlings are up"))
        if kind == "sow" and isinstance(germ, dict) and germ.get("min") is not None:
            best = f", best near {germ['opt']:g} °C" if germ.get("opt") is not None else ""
            out.append(("Soil temperature", f"at least {germ['min']:g} °C to germinate{best}"))
        if kind == "sow":
            out.append(("Comes up in", _emergence(item)))
        age = _num(item, "transplant_age_days")
        if kind == "set_out" and age:
            out.append(("Seedlings", f"about {round(age / 7)} weeks old when they go out"))
        out.append(
            (
                "Light",
                {
                    "full_sun": "full sun",
                    "partial_sun": "sun for part of the day",
                    "partial_shade": "part shade",
                    "shade": "shade",
                }.get(sun),
            )
        )
        if kind == "sow" and isinstance(cycle, dict):
            out.append(("Ready", f"{cycle['min']:.0f} to {cycle['max']:.0f} days from sowing"))
    elif kind == "harvest":
        height = _num(item, "height")
        if cycle and isinstance(cycle, dict):
            out.append(("Cycle", f"{cycle['min']:.0f} to {cycle['max']:.0f} days from sowing"))
        if height:
            out.append(("Grows to", _cm(height)))
    elif kind == "water":
        root = item.get("requirements", {}).get("water", {}).get("root_depth", {}).get("value")
        if isinstance(root, dict):
            out.append(("Roots reach", f"{root['min']:g} to {root['max']:g} m, so soak deep rather than often"))
    return [{"label": a, "text": b} for a, b in out if b]
