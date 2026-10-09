#!/usr/bin/env python3
"""Write catalog/schema/*.json (JSON Schema) from the Pydantic models in backend/app/catalog.py.

    python scripts/catalog_schema.py          # write
    python scripts/catalog_schema.py --check  # exit 1 if the files are out of date (CI)

Editors can use these for autocompletion, e.g. `# yaml-language-server: $schema=../schema/crop.json`.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.catalog import MODELS, Source  # noqa: E402


def schemas() -> dict[str, str]:
    out = {f"{kind}.json": model.model_json_schema() for kind, model in MODELS.items()}
    out["sources.json"] = {"type": "array", "items": Source.model_json_schema()}
    return {name: json.dumps(schema, indent=2, sort_keys=True) + "\n" for name, schema in out.items()}


def main() -> int:
    target = ROOT / "catalog" / "schema"
    stale = [
        name for name, text in schemas().items() if not (target / name).exists() or (target / name).read_text() != text
    ]
    if "--check" in sys.argv:
        if stale:
            print("catalog/schema is out of date; run: python scripts/catalog_schema.py\n  " + "\n  ".join(stale))
        return 1 if stale else 0
    target.mkdir(parents=True, exist_ok=True)
    for name, text in schemas().items():
        (target / name).write_text(text)
    print(f"wrote {len(schemas())} schema files to {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
