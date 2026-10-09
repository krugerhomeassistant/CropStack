"""Catalog ingestion (maintainers only; self-hosted servers never run this). SPEC §16.1.

    python scripts/ingest fetch   # download sources politely into .ingest-cache/, record them in snapshots.lock
    python scripts/ingest merge   # extract from the locked snapshots, merge into catalog/crops/*.yaml
    python scripts/ingest check   # compare crop scientific names and families with the GBIF Backbone

Review the resulting `git diff catalog/` like any other change; hand-curated values are never overwritten.
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

import extract
import fetch
import merge
import yaml

CATALOG = fetch.ROOT / "catalog"
CROSSWALK = yaml.safe_load(Path(__file__).with_name("crosswalk.yaml").read_text())

# Snapshot key -> URL. Pinned to a commit or a stable page so a re-fetch is comparable.
SOURCES = {
    "pyfao56-tables": "https://raw.githubusercontent.com/kthorp/pyfao56/main/src/pyfao56/tools/tables.py",
    "harrington-osu": "https://extension.oregonstate.edu/es/catalog/soil-temperature-conditions-vegetable-seed-germination",
    "openfarm-rescue": "https://raw.githubusercontent.com/thefullnacho/openfarm-crops-rescue/"
    "754cfd75da007c17a628eca812632f326dc7cf10/crops.json",
}


def gbif_url(name: str) -> str:
    return f"https://api.gbif.org/v1/species/match?name={quote(name)}&kingdom=Plantae&strict=true"


def cmd_fetch() -> int:
    with fetch.client() as client:
        for key, url in SOURCES.items():
            print(f"{key}: {fetch.fetch(key, url, client)[:12]}")
    return 0


def _source(key: str, ref: str) -> tuple[bytes, dict]:
    raw, entry = fetch.snapshot(key)
    return raw, merge.cite(ref, entry["retrieved"], entry["sha256"])


def cmd_merge() -> int:
    raw, fao_src = _source("pyfao56-tables", "fao-56")
    fao = extract.fao56(raw)
    raw, harr_src = _source("harrington-osu", "harrington-osu")
    harr = extract.harrington(raw)
    raw, of_src = _source("openfarm-rescue", "openfarm-rescue")
    openfarm = extract.openfarm(raw)

    for slug, names in CROSSWALK.items():
        path = CATALOG / "crops" / f"{slug}.yaml"
        if not path.exists():
            print(f"skip {slug}: no {path.relative_to(fetch.ROOT)} (write the curated base first)")
            continue
        item = yaml.safe_load(path.read_text())
        stages = [s for s in fao["stages"] if s["crop"] == names.get("fao56_stages")]
        batches = [
            ("fao-56", merge.from_fao56(stages, fao["kc"].get(names.get("fao56_kc")), fao["roots"].get(names.get("fao56_roots")), fao_src)),
            ("harrington-osu", merge.from_harrington(harr["germination"].get(names.get("harrington")), harr["emergence"].get(names.get("harrington")), harr_src)),
            ("openfarm-rescue", merge.from_openfarm(openfarm.get(names.get("openfarm")), of_src)),
        ]  # fmt: skip
        changed = [p for ref, proposals in batches for p in merge.merge(item, proposals, ref)]
        text = merge.dump(item)
        if text != path.read_text():  # also normalises formatting
            path.write_text(text)
            print(f"{slug}: {len(changed)} field(s) updated")
    return 0


def cmd_check() -> int:
    problems = 0
    with fetch.client() as client:
        for slug, names in CROSSWALK.items():
            path = CATALOG / "crops" / f"{slug}.yaml"
            if not path.exists() or "gbif" not in names:
                continue
            item = yaml.safe_load(path.read_text())
            key = f"gbif:{names['gbif']}"
            fetch.fetch(key, gbif_url(names["gbif"]), client)
            match = extract.gbif_match(fetch.snapshot(key)[0])
            if match["status"] != names.get("gbif_status", "ACCEPTED") or match["name"] != item["scientific_name"]:
                print(f"{slug}: GBIF says {match['name']} ({match['status']}), catalog has {item['scientific_name']}")
                problems += 1
            if match["family"] != item["family"]:
                print(f"{slug}: GBIF family {match['family']}, catalog has {item['family']}")
                problems += 1
    print(f"{problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    commands = {"fetch": cmd_fetch, "merge": cmd_merge, "check": cmd_check}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        print(__doc__)
        sys.exit(2)
    sys.exit(commands[sys.argv[1]]())
