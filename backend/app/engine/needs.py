"""What a household eats: a weekly target of produce per food group, and how much of it a supply meets. Pure."""

from __future__ import annotations

from datetime import date, timedelta

BASKET_KG_PER_PERSON_DAY = 0.4  # WHO: at least 400 g of fruit and vegetables a day
GROUP_SHARE = {  # our own split of that basket, by how a crop is eaten; not nutrition advice
    "leafy": 0.20,
    "fruiting": 0.20,
    "root": 0.15,
    "brassica": 0.12,
    "legume": 0.10,
    "squash": 0.10,
    "allium": 0.08,
    "herb": 0.05,
}
GROUPS = tuple(GROUP_SHARE)
WEEKS = 52
SHORT_FRACTION = 0.5  # a week counts as short when it has less than this share of its target


def weekly_target(people: int) -> dict[str, float]:
    """Kilograms of each group the household eats in a week."""
    return {g: people * 7 * BASKET_KG_PER_PERSON_DAY * s for g, s in GROUP_SHARE.items()}


def week_range(today: date, first: date, last: date) -> range:
    """Week numbers (0 = the week starting today) that a harvest from `first` to `last` touches, inside the year."""
    return range(max(0, (first - today).days // 7), min(WEEKS - 1, (last - today).days // 7) + 1)


def spread(today: date, first: date, last: date, kg: float) -> dict[int, float]:
    """`kg` harvested evenly from `first` to `last`: kg per week number, for the weeks inside the year only.
    ponytail: even spread; a real harvest curve (slow start, peak, tail) needs crop data we do not have."""
    weeks = max(1, (last - today).days // 7 - (first - today).days // 7 + 1)  # today-aligned buckets, unclipped
    return {w: kg / weeks for w in week_range(today, first, last)}


def coverage(target: dict[str, float], supply: dict[str, list[float]], today: date) -> dict:
    """How much of the weekly target the supply meets. A surplus one week does not make up for a gap in another."""
    groups, overall = {}, 0.0
    for g in GROUPS:
        need = target[g] * WEEKS
        covered = sum(min(s, target[g]) for s in supply[g]) / need if need else 1.0
        overall += GROUP_SHARE[g] * covered
        groups[g] = {
            "target_kg": round(need, 1),
            "supply_kg": round(sum(supply[g]), 1),
            "covered": round(covered, 3),
            "weeks_short": [
                (today + timedelta(weeks=i)).isoformat()
                for i, s in enumerate(supply[g])
                if s < target[g] * SHORT_FRACTION
            ],
        }
    return {"overall": round(overall, 3), "groups": groups}
