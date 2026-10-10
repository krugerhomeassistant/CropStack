from datetime import UTC, datetime

from app.engine.layout import bed_use, footprint_m2
from tests.test_household import owner  # noqa: F401  (fixture)


def fact(value, unit="cm"):
    return {"value": value, "unit": unit}


def test_footprint_uses_spread_and_row_spacing_in_metres():
    assert footprint_m2({"params": {"plant_spread": fact(30), "row_spacing": fact(45)}}) == 0.3 * 0.45
    assert footprint_m2({"params": {"plant_spread": fact(0.5, "m")}}) == 0.25  # no row gap: spread squared
    assert footprint_m2({"params": {"row_spacing": fact(45)}}) is None


def test_bed_use_flags_a_full_bed_and_counts_unknowns():
    assert not bed_use(1.0, [(4, 0.25)]).crowded
    full = bed_use(1.0, [(5, 0.25), (2, None)])
    assert full.crowded and full.unknown == 2 and full.needed_m2 == 1.25


def test_beds_hold_plantings_and_say_when_they_are_full(owner):  # noqa: F811
    bed = owner.post("/api/v1/beds", json={"name": "Bed 1", "width": 1.0, "length": 1.0, "x": 0.5, "y": 0.5}).json()
    today = str(datetime.now(UTC).date())
    made = owner.post(
        "/api/v1/plantings", json={"crop": "testcrop", "method": "direct", "start_date": today, "bed_id": bed["id"]}
    ).json()
    assert made["location"] == "Bed 1"
    [row] = owner.get("/api/v1/beds").json()
    assert row["plantings"] == [made["id"]] and row["area_m2"] == 1.0

    owner.patch(f"/api/v1/beds/{bed['id']}", json={"name": "Herb bed", "x": 2})
    assert owner.get("/api/v1/plantings").json()[0]["location"] == "Herb bed"
    assert owner.get("/api/v1/beds").json()[0]["x"] == 2

    assert (
        owner.post(
            "/api/v1/plantings", json={"crop": "testcrop", "method": "direct", "start_date": today, "bed_id": 999}
        ).status_code
        == 422
    )
    assert owner.delete(f"/api/v1/beds/{bed['id']}").status_code == 204
    assert owner.get("/api/v1/plantings").json()[0]["bed_id"] is None  # the planting stays
    assert owner.post("/api/v1/beds", json={"name": "x", "width": 0, "length": 1}).status_code == 422


def plant(client, bed, cells, start, **extra):
    return client.post(
        "/api/v1/plantings",
        json={"crop": "testcrop", "method": "direct", "start_date": start, "bed_id": bed, "cells": cells} | extra,
    )


def test_cells_hold_different_crops_over_time_and_clash_only_when_dates_overlap(owner):  # noqa: F811
    bed = owner.post(
        "/api/v1/beds", json={"name": "Row", "kind": "row", "width": 0.6, "length": 1.5, "cell_cm": 30}
    ).json()
    assert (owner.get("/api/v1/beds").json()[0]["cols"], owner.get("/api/v1/beds").json()[0]["rows"]) == (2, 5)

    first = plant(owner, bed["id"], [[0, 0], [1, 0]], "2026-10-01", ends_on="2026-11-30")
    assert first.status_code == 201 and first.json()["quantity"] == 2  # one plant per cell when no spread is catalogued
    later = plant(owner, bed["id"], [[0, 0]], "2026-12-01", ends_on="2027-02-01")  # same cell, after the first is done
    assert later.status_code == 201
    assert owner.get("/api/v1/beds").json()[0]["clashes"] == []

    overlap = plant(owner, bed["id"], [[1, 0]], "2026-11-15", ends_on="2027-01-01")
    assert overlap.status_code == 201
    [row] = owner.get("/api/v1/beds").json()
    assert row["crowded"] and [c["cell"] for c in row["clashes"]] == [[1, 0]]
    assert {p["planting_id"] for p in row["placements"]} == {
        first.json()["id"],
        later.json()["id"],
        overlap.json()["id"],
    }


def test_cells_are_never_refused_for_the_grid_and_follow_a_bed_that_shrinks(owner):  # noqa: F811
    bed = owner.post("/api/v1/beds", json={"name": "B", "width": 1.2, "length": 1.2}).json()  # 4 x 4 cells
    assert plant(owner, bed["id"], [[-1, 0]], "2026-10-01").status_code == 422
    assert plant(owner, bed["id"], [[4, 0]], "2026-10-01").status_code == 201  # outside the grid: kept, not refused
    assert (
        owner.post(
            "/api/v1/plantings",
            json={"crop": "testcrop", "method": "direct", "start_date": "2026-10-01", "cells": [[0, 0]]},
        ).status_code
        == 422
    )
    made = plant(owner, bed["id"], [[0, 0], [3, 3]], "2026-10-01").json()
    owner.patch(f"/api/v1/beds/{bed['id']}", json={"width": 0.6, "length": 0.6})  # now 2 x 2

    def mine():
        return next(p for p in owner.get("/api/v1/plantings").json() if p["id"] == made["id"])["cells"]

    assert mine() == [[0, 0], [3, 3]]  # kept, shown as outside
    owner.patch(f"/api/v1/plantings/{made['id']}", json={"cells": [[1, 1]]})
    assert mine() == [[1, 1]]
    owner.patch(f"/api/v1/plantings/{made['id']}", json={"bed_id": None})
    assert mine() == []


def test_recommendations_without_a_garden_are_empty(owner):  # noqa: F811
    assert owner.get("/api/v1/recommendations").json() == {"garden": False, "now": [], "soon": []}


def test_a_bed_remembers_its_layout_and_can_leave_it(owner):  # noqa: F811
    bed = owner.post("/api/v1/beds", json={"name": "A", "width": 1, "length": 2, "layout": "Back garden"}).json()
    assert bed["layout"] == "Back garden"
    assert owner.patch(f"/api/v1/beds/{bed['id']}", json={"layout": ""}).json()["layout"] == ""


def test_a_planting_can_be_moved_in_time_and_resized_from_the_bed(owner):  # noqa: F811
    bed = owner.post("/api/v1/beds", json={"name": "A", "width": 1, "length": 1}).json()
    made = plant(owner, bed["id"], [[0, 0]], "2026-10-01").json()
    url = f"/api/v1/plantings/{made['id']}"
    moved = owner.patch(url, json={"start_date": "2026-11-05", "quantity": 7}).json()
    assert (moved["start_date"], moved["quantity"]) == ("2026-11-05", 7)
    assert owner.patch(url, json={"start_date": None}).json()["start_date"] == "2026-11-05"  # cannot be cleared
    assert owner.patch(url, json={"set_out_date": "2026-12-01"}).json()["set_out_date"] is None  # direct: none
    seen = owner.get("/api/v1/beds").json()[0]["placements"][0]
    assert seen["start_date"] == "2026-11-05" and seen["method"] == "direct"


def test_a_planting_dated_in_the_past_is_already_growing_and_has_an_outlook(owner):  # noqa: F811
    from datetime import timedelta

    today = datetime.now(UTC).date()
    week_ago, two_weeks = str(today - timedelta(days=7)), str(today - timedelta(days=14))
    sown = owner.post("/api/v1/plantings", json={"crop": "testcrop", "method": "direct", "start_date": week_ago})
    assert sown.json()["status"] == "sown"
    out = owner.post(
        "/api/v1/plantings",
        json={"crop": "testcrop", "method": "transplant", "start_date": two_weeks, "set_out_date": week_ago},
    )
    assert out.json()["status"] == "transplanted"
    planned = owner.post("/api/v1/plantings", json={"crop": "testcrop", "method": "direct", "start_date": str(today)})
    assert planned.json()["status"] == "planned"
    rows = {r["id"]: r for r in owner.get("/api/v1/plantings").json()}
    assert rows[sown.json()["id"]]["harvest_from"] and rows[planned.json()["id"]]["next_job"]["title"].startswith("Sow")


def test_changing_a_bed_never_throws_away_where_things_grow(owner):  # noqa: F811
    from app.engine.layout import remap

    assert remap([[1, 0]], 30, 15) == [[2, 0], [3, 0], [2, 1], [3, 1]]
    assert remap([[2, 0], [3, 0]], 15, 30) == [[1, 0]]
    bed = owner.post("/api/v1/beds", json={"name": "Keep", "width": 1.2, "length": 1.2}).json()
    made = plant(owner, bed["id"], [[0, 0], [3, 3]], "2026-10-01").json()
    url = f"/api/v1/beds/{bed['id']}"
    owner.patch(
        url, json={"name": "Keep", "width": 1.2, "length": 1.2, "cell_cm": 30, "layout": "Front"}
    )  # unchanged size
    owner.patch(url, json={"width": 0.6})  # smaller: the cell at column 3 is outside but kept
    mine = next(p for p in owner.get("/api/v1/plantings").json() if p["id"] == made["id"])
    assert mine["cells"] == [[0, 0], [3, 3]]
    shown = next(b for b in owner.get("/api/v1/beds").json() if b["id"] == bed["id"])
    assert shown["outside"] == 1
    erased = owner.patch(f"/api/v1/plantings/{made['id']}", json={"cells": [[3, 3]]})  # erase inside, keep outside
    assert erased.status_code == 200
    owner.patch(url, json={"cell_cm": 60})
    mine = next(p for p in owner.get("/api/v1/plantings").json() if p["id"] == made["id"])
    assert mine["cells"] == [[1, 1]]
