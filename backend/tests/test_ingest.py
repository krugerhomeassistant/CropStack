"""Catalog ingestion (scripts/ingest): extractors on synthetic fixtures shaped like the real sources, and the merge
rule that hand-curated values always win. Fixtures are made up so no third-party text is committed."""

import json
import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "ingest"))

import extract
import merge

from app.catalog import Crop

PYFAO56 = b'''
class FAO56Tables:
    def __init__(self):
        table11data = """
            tomato                       ,  30,  40,  40,   25,  135, jan             , arid region
            tomato                       ,  35,  45,  70,   30,  180, oct nov         , arid region
            alfalfa total season         ,  10,  30,    ,     ,     ,
        """
        table12data = """
            small vegetables             , 0.7 , 1.05, 0.95,
            tomato                       , 0.6 , 1.15, 0.80, 0.6
        """
        table22data = """
            tomato                       , 0.7,   1.5, 0.40
        """
'''

HARRINGTON = b"""
<table><tr><th>Crop</th><th>Minimum</th><th>Optimum Range</th><th>Optimum</th><th>Maximum</th></tr>
<tr><td>Tomato</td><td>50</td><td>60&ndash;85</td><td>85</td><td>95</td></tr>
<tr><td>Typo</td><td>90</td><td>45&ndash;5</td><td>40</td><td>100</td></tr></table>
<table><tr><th>Crop</th><th>32</th><th>50</th><th>77</th></tr>
<tr><td>Tomato</td><td>Little or no germination</td><td>43</td><td>6</td></tr></table>
"""

SOURCE = merge.cite("fao-56", date(2026, 10, 9), "ab" * 32)


def test_fao56_tables():
    tables = extract.fao56(PYFAO56)
    assert [s["mid"] for s in tables["stages"] if s["crop"] == "tomato"] == [40, 70]
    assert all(s["crop"] != "alfalfa total season" for s in tables["stages"])  # incomplete rows dropped
    assert tables["kc"]["tomato"] == {"initial": 0.6, "mid": 1.15, "late": 0.8, "height_max": 0.6}
    assert tables["kc"]["small vegetables"]["height_max"] is None
    assert tables["roots"]["tomato"] == {"root_min": 0.7, "root_max": 1.5, "p": 0.4}


def test_harrington_converts_and_skips():
    data = extract.harrington(HARRINGTON)
    assert data["germination"] == {"Tomato": {"min": 10.0, "opt": 29.4, "max": 35.0}}  # out-of-order row skipped
    assert data["emergence"]["Tomato"] == {10.0: 43, 25.0: 6}  # "Little or no germination" left out


def test_openfarm_drops_empty_and_tiny():
    raw = json.dumps(
        [
            {
                "slug": "onion",
                "rowSpacingCm": 15,
                "spreadCm": 0,
                "heightCm": 1,
                "sun": "Full Sun",
                "source": {"waybackUrl": "https://web.archive.org/x"},
            }
        ]
    ).encode()
    record = extract.openfarm(raw)["onion"]
    assert "spread" not in record
    proposals = merge.from_openfarm(record, merge.cite("openfarm-rescue", date(2026, 10, 9), "cd" * 32))
    assert set(proposals) == {"params.row_spacing", "params.sun"}  # 1 cm height is an entry error
    assert proposals["params.sun"]["value"] == "full_sun"
    assert proposals["params.row_spacing"]["evidence"] == "grower-reported"


def test_proposals_validate_against_the_catalog_model():
    tables = extract.fao56(PYFAO56)
    stages = [s for s in tables["stages"] if s["crop"] == "tomato"]
    item = {"kind": "crop", "slug": "tomato", "names": {"en": ["Tomato"]}, "scientific_name": "Solanum lycopersicum"}
    item |= {"family": "Solanaceae", "life_cycle": "annual"}
    merge.merge(item, merge.from_fao56(stages, tables["kc"]["tomato"], tables["roots"]["tomato"], SOURCE), "fao-56")
    harr = extract.harrington(HARRINGTON)
    harr_src = merge.cite("harrington-osu", date(2026, 10, 9), "ef" * 32)
    merge.merge(item, merge.from_harrington(harr["germination"]["Tomato"], harr["emergence"]["Tomato"], harr_src), "x")
    crop = Crop.model_validate(yaml.safe_load(merge.dump(item)))  # the YAML round trip is what lands in catalog/
    assert crop.requirements.water.kc_mid.value == 1.15
    assert crop.requirements.soil_temperature.germination.value.opt == 29.4
    assert len(crop.params["stage_days_mid"]) == 2
    assert "&id" not in merge.dump(item)  # no YAML anchors for repeated dates


def test_merge_never_overwrites_curated_values():
    curated = {"value": 1.2, "unit": "1", "evidence": "peer-reviewed", "sources": [{"ref": "some-study"}]}
    item = {"requirements": {"water": {"kc_mid": curated}}}
    proposal = {"requirements.water.kc_mid": merge.value(1.15, "1", "government", SOURCE)}
    assert merge.merge(item, proposal, "fao-56") == []
    assert item["requirements"]["water"]["kc_mid"] is curated


def test_merge_refreshes_its_own_values():
    item = {"requirements": {"water": {"kc_mid": merge.value(1.1, "1", "government", SOURCE)}}}
    newer = {"requirements.water.kc_mid": merge.value(1.15, "1", "government", SOURCE)}
    assert merge.merge(item, newer, "fao-56") == ["requirements.water.kc_mid"]
    assert item["requirements"]["water"]["kc_mid"]["value"] == 1.15
    assert merge.merge(item, newer, "fao-56") == []  # unchanged → no diff


def ecocrop_row(**changes):
    """A row shaped like Recocrop's ecocrop table (made-up numbers)."""
    row = {"CODE": 99, "NAME": "Testbean", "SCIENTNAME": "Fabaceae test", "GMIN": 70, "GMAX": 150, "KTMP": 0}
    row |= dict(TMIN=7, TOPMN=20, TOPMX=27, TMAX=35, RMIN=400, ROPMN=600, ROPMX=1300, RMAX=1800)
    row |= dict(PHMIN=5.0, PHOPMN=5.5, PHOPMX=6.8, PHMAX=7.5)
    return row | changes


def test_ecocrop_keeps_only_ordered_ranges():
    rows = [
        ecocrop_row(),
        ecocrop_row(CODE=100, RMIN=0, ROPMN=0, ROPMX=0, RMAX=0),  # 0 = not given
        ecocrop_row(CODE=101, PHMIN=float("nan")),
        ecocrop_row(CODE=102, TOPMN=30, TOPMX=27),  # out of order
        ecocrop_row(CODE=103, GMIN=0, GMAX=0),
    ]
    records = extract.ecocrop(rows)
    assert records[99]["temperature"] == {"min": 7, "opt_min": 20, "opt_max": 27, "max": 35}
    assert records[99]["cycle"] == {"min": 70, "max": 150}
    assert "rainfall" not in records[100]
    assert "ph" not in records[101]
    assert "temperature" not in records[102] and "ph" in records[102]
    assert "cycle" not in records[103]
    assert "ktmp" not in str(records).lower()  # KTMP's 0 is ambiguous, so it is never read


def test_ecocrop_proposals_validate_against_the_catalog_model():
    src = merge.cite("fao-ecocrop", date(2026, 10, 9), "12" * 32)
    proposals = merge.from_ecocrop(extract.ecocrop([ecocrop_row()])[99], 99, src)
    item = {"kind": "crop", "slug": "testbean", "names": {"en": ["Testbean"]}, "scientific_name": "Phaseolus test"}
    item |= {"family": "Fabaceae", "life_cycle": "annual"}
    merge.merge(item, proposals, "fao-ecocrop")
    crop = Crop.model_validate(yaml.safe_load(merge.dump(item)))
    assert crop.requirements.temperature.stress_min.value == 7
    assert (crop.requirements.temperature.optimal.value.min, crop.requirements.temperature.optimal.value.max) == (
        20,
        27,
    )
    assert crop.requirements.soil.ph.value.opt_max == 6.8
    assert crop.params["annual_rainfall"].unit == "mm"
    assert crop.params["cycle_days"].sources[0].locator == "ECOCROP code 99, GMIN, GMAX (via Recocrop)"
    assert merge.from_ecocrop(None, None, src) == {}
