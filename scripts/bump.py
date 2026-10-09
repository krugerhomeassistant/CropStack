#!/usr/bin/env python3
"""Bump the version everywhere and cut the changelog section.

    python scripts/bump.py 0.2.0
    git commit -am "Release v0.2.0" && git push

When a version with no GitHub release reaches main, CI runs every check, publishes
ghcr.io/krugerhomeassistant/cropstack:0.2.0 (+ 0.2 and latest), then creates the v0.2.0 tag and release.
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/krugerhomeassistant/CropStack"


def main(version: str) -> None:
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        sys.exit("usage: bump.py X.Y.Z")
    (ROOT / "backend/app/__init__.py").write_text(f'VERSION = "{version}"\n')

    for name in ("package.json", "package-lock.json"):
        path = ROOT / "frontend" / name
        data = json.loads(path.read_text())
        data["version"] = version
        if "packages" in data:
            data["packages"][""]["version"] = version
        path.write_text(json.dumps(data, indent=2) + "\n")

    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text()
    if f"## [{version}]" not in text:
        prev = re.search(r"## \[(\d+\.\d+\.\d+)\]", text)
        text = text.replace("## [Unreleased]\n", f"## [Unreleased]\n\n## [{version}] - {date.today()}\n", 1)
        compare = f"{REPO}/compare/v{prev.group(1)}...v{version}" if prev else f"{REPO}/releases/tag/v{version}"
        text = re.sub(
            r"\[Unreleased\]: .*\n",
            f"[Unreleased]: {REPO}/compare/v{version}...HEAD\n[{version}]: {compare}\n",
            text,
        )
        changelog.write_text(text)
    print(f"Bumped to {version}. Review CHANGELOG.md, then commit and push to main to release v{version}.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
