"""Turn extractor records into cited catalog values and merge them into crop files. Pure: no I/O, no network.

Hand-curated values always win (SPEC §16.1): a proposal only fills an empty field, or replaces a field whose
values cite nothing but the same source (so a re-run refreshes what the pipeline itself wrote earlier).
"""

from __future__ import annotations

from datetime import date
from typing import Any

import yaml

Proposals = dict[str, Any]  # field path ("requirements.water.kc_mid") -> Value dict or list of Value dicts


def cite(ref: str, retrieved: date, sha256: str, locator: str | None = None) -> dict:
    out = {"ref": ref, "retrieved": retrieved, "snapshot": f"sha256:{sha256}"}
    if locator:
        out["locator"] = locator
    return out


def value(v: Any, unit: str | None, evidence: str, source: dict, confidence: str = "medium", **qualifiers) -> dict:
    out: dict[str, Any] = {"value": v}
    if unit:
        out["unit"] = unit
    if qualifiers:
        out["qualifiers"] = qualifiers
    out.update(evidence=evidence, confidence=confidence, sources=[source])
    return out


# ---------------------------------------------------------------- proposals per source


def from_harrington(row: dict | None, emergence: dict | None, source: dict) -> Proposals:
    out: Proposals = {}
    if row:
        out["requirements.soil_temperature.germination"] = value(
            {"min": row["min"], "opt": row["opt"], "max": row["max"]},
            "Cel",
            "extension-service",
            {**source, "locator": "Table 1 (°F converted to °C)"},
        )
    if emergence:
        out["params.days_to_emergence"] = [
            value(days, "d", "extension-service", {**source, "locator": "Table 2"}, soil_temp_c=temp)
            for temp, days in sorted(emergence.items())
        ]
    return out


def from_fao56(stages: list[dict], kc: dict | None, roots: dict | None, source: dict) -> Proposals:
    out: Proposals = {}

    def at(table: int) -> dict:
        return {**source, "locator": f"Table {table} (via pyfao56)"}

    if kc:
        for key in ("initial", "mid", "late"):
            if kc[key] is not None:
                out[f"requirements.water.kc_{key}"] = value(kc[key], "1", "government", at(12), "high")
        if kc["height_max"] is not None:
            out["params.height_max"] = value(kc["height_max"], "m", "government", at(12))
    if roots:
        if roots["root_min"] is not None and roots["root_max"] is not None:
            depth = {"min": roots["root_min"], "max": roots["root_max"]}
            out["requirements.water.root_depth"] = value(depth, "m", "government", at(22), "high")
        if roots["p"] is not None:
            out["requirements.water.depletion_fraction"] = value(roots["p"], "1", "government", at(22), "high")
    for stage in ("initial", "development", "mid", "late"):
        rows = [
            value(s[stage], "d", "government", at(11), region=s["region"], planting=s["planting"])
            for s in stages
            if s[stage] is not None
        ]
        if rows:
            out[f"params.stage_days_{stage}"] = rows
    return out


def from_ecocrop(record: dict | None, code: int | None, source: dict) -> Proposals:
    """FAO ECOCROP limits. Air temperature maps onto the profile's stress and optimum fields; rainfall, pH and cycle
    length are kept as ranges (annual rainfall is a range to compare with, not a rule)."""
    if not record or code is None:
        return {}

    def at(column: str) -> dict:
        return {**source, "locator": f"ECOCROP code {code}, {column} (via Recocrop)"}

    out: Proposals = {}
    if t := record.get("temperature"):
        out["requirements.temperature.stress_min"] = value(t["min"], "Cel", "government", at("TMIN"))
        out["requirements.temperature.optimal"] = value(
            {"min": t["opt_min"], "max": t["opt_max"]}, "Cel", "government", at("TOPMN, TOPMX")
        )
        out["requirements.temperature.stress_max"] = value(t["max"], "Cel", "government", at("TMAX"))
    if ph := record.get("ph"):
        out["requirements.soil.ph"] = value(ph, None, "government", at("PHMIN to PHMAX"))
    if rain := record.get("rainfall"):
        out["params.annual_rainfall"] = value(rain, "mm", "government", at("RMIN to RMAX"))
    if cycle := record.get("cycle"):
        out["params.cycle_days"] = value(cycle, "d", "government", at("GMIN, GMAX"))
    return out


SUN = {"Full Sun": "full_sun", "Partial Sun": "partial_sun", "Partial Shade": "partial_shade", "Shade": "shade"}


def from_openfarm(record: dict | None, source: dict) -> Proposals:
    if not record:
        return {}
    src = {**source, "locator": record["wayback"]}
    out: Proposals = {}
    for field, key in (("row_spacing", "row_spacing"), ("plant_spread", "spread")):
        if key in record:
            out[f"params.{field}"] = value(record[key], "cm", "grower-reported", src, "low")
    if record.get("height", 0) >= 5:  # smaller values in the rescue set are entry errors (e.g. onion: 1 cm)
        out["params.height"] = value(record["height"], "cm", "grower-reported", src, "low")
    if record.get("sun") in SUN:
        out["params.sun"] = value(SUN[record["sun"]], None, "grower-reported", src, "low")
    return out


# ---------------------------------------------------------------- merge


def _get(data: dict, path: str) -> Any:
    for key in path.split("."):
        if not isinstance(data, dict) or key not in data:
            return None
        data = data[key]
    return data


def _set(data: dict, path: str, new: Any) -> None:
    *parents, last = path.split(".")
    for key in parents:
        data = data.setdefault(key, {})
    data[last] = new


def _refs(fact: Any) -> set[str]:
    values = fact if isinstance(fact, list) else [fact]
    return {s["ref"] for v in values if isinstance(v, dict) for s in v.get("sources", [])}


def merge(item: dict, proposals: Proposals, ref: str) -> list[str]:
    """Apply proposals from source `ref` to item in place; returns the changed field paths."""
    changed = []
    for path, new in proposals.items():
        old = _get(item, path)
        if old is None or (_refs(old) == {ref} and old != new):
            _set(item, path, new)
            changed.append(path)
    return changed


# ---------------------------------------------------------------- YAML output


class _Dumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:  # repeated dates would otherwise become &id001 anchors
        return True


SOURCE_ORDER = ("ref", "locator", "retrieved", "snapshot")


def _dict(dumper: yaml.SafeDumper, data: dict) -> yaml.Node:
    if "ref" in data and set(data) <= set(SOURCE_ORDER):
        data = {k: data[k] for k in SOURCE_ORDER if k in data}
    flat = all(not isinstance(v, dict | list) for v in data.values())
    return dumper.represent_mapping("tag:yaml.org,2002:map", data, flow_style=flat and len(data) <= 5)


_Dumper.add_representer(dict, _dict)


def dump(item: dict) -> str:
    return yaml.dump(item, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=120)
