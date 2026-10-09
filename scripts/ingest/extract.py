"""Pure extractors: raw snapshot bytes → plain records. No network, no catalog knowledge; tested on fixtures.

Each extractor keeps the source's own crop names; crosswalk.yaml maps them to CropStack slugs.
"""

from __future__ import annotations

import html
import json
import re


def _number(cell: str) -> float | None:
    try:
        return float(cell)
    except ValueError:
        return None


# ---------------------------------------------------------------- FAO-56 tables via pyfao56 (tools/tables.py)


def _table_rows(text: str, name: str) -> list[list[str]]:
    match = re.search(rf'{name}data\s*=\s*"""(.*?)"""', text, re.S)
    if not match:
        raise ValueError(f"{name} not found in pyfao56 tables.py")
    return [[c.strip() for c in line.split(",")] for line in match.group(1).strip().splitlines() if line.strip()]


def fao56(raw: bytes) -> dict:
    """Tables 11 (stage lengths, d), 12 (single Kc, max height m) and 22 (max root depth m, depletion fraction p)."""
    text = raw.decode()
    stages = [
        {
            "crop": r[0],
            "initial": _number(r[1]),
            "development": _number(r[2]),
            "mid": _number(r[3]),
            "late": _number(r[4]),
            "planting": r[6] or None,
            "region": r[7] or None,
        }
        for r in _table_rows(text, "table11")
        if len(r) >= 8 and None not in (_number(r[1]), _number(r[2]), _number(r[3]), _number(r[4]))
    ]
    kc = {
        r[0]: {"initial": _number(r[1]), "mid": _number(r[2]), "late": _number(r[3]), "height_max": _number(r[4])}
        for r in _table_rows(text, "table12")
        if len(r) >= 5
    }
    roots = {
        r[0]: {"root_min": _number(r[1]), "root_max": _number(r[2]), "p": _number(r[3])}
        for r in _table_rows(text, "table22")
        if len(r) >= 4
    }
    return {"stages": stages, "kc": kc, "roots": roots}


# ---------------------------------------------------------------- Harrington germination tables (OSU Extension page)


def _cells(row: str) -> list[str]:
    return [html.unescape(re.sub(r"<.*?>", "", c)).strip() for c in re.findall(r"<t[hd].*?</t[hd]>", row, re.S)]


def _f_to_c(f: float) -> float:
    return round((f - 32) * 5 / 9, 1)


def harrington(raw: bytes) -> dict:
    """Table 1: soil temperature for germination (min, optimum, max). Table 2: days to emergence by soil temperature.

    Returns °C. Rows whose min/opt/max are out of order are skipped (the page has at least one typo, in an
    optimum range), and cells reading "Little or no germination" / "Not tested" are left out.
    """
    tables = re.findall(r"<table.*?</table>", raw.decode(), re.S)
    if len(tables) < 2:
        raise ValueError("expected two tables on the Harrington page")

    germination: dict[str, dict] = {}
    for row in re.findall(r"<tr.*?</tr>", tables[0], re.S)[1:]:
        cells = _cells(row)
        if len(cells) != 5:
            continue
        low, opt, high = (_number(cells[i]) for i in (1, 3, 4))
        if None in (low, opt, high) or not low <= opt <= high:
            continue
        germination[cells[0]] = {"min": _f_to_c(low), "opt": _f_to_c(opt), "max": _f_to_c(high)}

    rows = re.findall(r"<tr.*?</tr>", tables[1], re.S)
    temps_f = [_number(c) for c in _cells(rows[0])[1:]]
    emergence: dict[str, dict[float, float]] = {}
    for row in rows[1:]:
        cells = _cells(row)
        days = {_f_to_c(t): _number(d) for t, d in zip(temps_f, cells[1:], strict=False) if t is not None}
        emergence[cells[0]] = {t: d for t, d in days.items() if d is not None}
    return {"germination": germination, "emergence": emergence}


# ---------------------------------------------------------------- OpenFarm rescue (crops.json, CC0)


def openfarm(raw: bytes) -> dict[str, dict]:
    """Records by OpenFarm slug, only the fields CropStack uses (cm). Zero or missing values are dropped."""
    out = {}
    for record in json.loads(raw):
        fields = {
            "row_spacing": record.get("rowSpacingCm"),
            "spread": record.get("spreadCm"),
            "height": record.get("heightCm"),
            "sun": record.get("sun"),
        }
        out[record["slug"]] = {
            "wayback": record["source"]["waybackUrl"],
            **{k: v for k, v in fields.items() if v not in (None, 0, "None", "")},
        }
    return out


# ---------------------------------------------------------------- GBIF species match


def gbif_match(raw: bytes) -> dict:
    record = json.loads(raw)
    return {
        "name": record.get("canonicalName"),
        "family": record.get("family"),
        "status": record.get("status"),
        "match": record.get("matchType"),
    }
