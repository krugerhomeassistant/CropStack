"""AC-P1 (SPEC §2): no code path may branch on where a garden is or what kind of climate it has.

Decisions come from requirement profiles combined with environment data. This scans the app source for the shapes such
presets take. Comments and docstrings may still *mention* hemispheres or climates; code may not test them.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [*ROOT.glob("backend/app/**/*.py"), *ROOT.glob("frontend/src/**/*.ts"), *ROOT.glob("frontend/src/**/*.tsx")]

BANNED = [
    (r"latitude\s*[<>]=?\s*-?0\b", "branching on the sign of the latitude (hemisphere)"),
    (r"\bhemisphere\w*\s*(==|!=|===|!==|\?)", "branching on a hemisphere"),
    (r"\bcountry(_?code)?\s*(==|!=|===|!==|in\b)", "branching on a country"),
    (r"['\"](mediterranean|tropical|temperate|arid|subtropical|continental|boreal)['\"]", "a climate-type preset"),
    (r"\b(HOT|COLD)_[CF]\b", "a global hot/cold threshold"),
]


def code_lines(path: Path):
    in_docstring = False
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        stripped = line.strip()
        if path.suffix == ".py" and stripped.count('"""') % 2 == 1:
            in_docstring = not in_docstring
            continue
        if in_docstring or stripped.startswith(("#", "//", "*", "/*")):
            continue
        yield number, line


def test_no_location_or_climate_presets_in_code():
    hits = [
        f"{path.relative_to(ROOT)}:{number}: {why}: {line.strip()}"
        for path in SOURCES
        for number, line in code_lines(path)
        for pattern, why in BANNED
        if re.search(pattern, line, re.IGNORECASE)
    ]
    assert not hits, "Presets are not allowed (SPEC P1):\n" + "\n".join(hits)


def test_the_check_catches_a_preset():
    assert re.search(BANNED[0][0], "if site.latitude < 0:")
    assert re.search(BANNED[3][0], "zone_type = 'Mediterranean'", re.IGNORECASE)
