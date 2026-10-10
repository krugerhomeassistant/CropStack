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


def test_cells_must_be_inside_the_bed_and_follow_it_when_it_shrinks(owner):  # noqa: F811
    bed = owner.post("/api/v1/beds", json={"name": "B", "width": 1.2, "length": 1.2}).json()  # 4 x 4 cells
    assert plant(owner, bed["id"], [[4, 0]], "2026-10-01").status_code == 422
    assert (
        owner.post(
            "/api/v1/plantings",
            json={"crop": "testcrop", "method": "direct", "start_date": "2026-10-01", "cells": [[0, 0]]},
        ).status_code
        == 422
    )
    made = plant(owner, bed["id"], [[0, 0], [3, 3]], "2026-10-01").json()
    owner.patch(f"/api/v1/beds/{bed['id']}", json={"width": 0.6, "length": 0.6})  # now 2 x 2
    assert owner.get("/api/v1/plantings").json()[0]["cells"] == [[0, 0]]
    owner.patch(f"/api/v1/plantings/{made['id']}", json={"cells": [[1, 1]]})
    assert owner.get("/api/v1/plantings").json()[0]["cells"] == [[1, 1]]
    owner.patch(f"/api/v1/plantings/{made['id']}", json={"bed_id": None})
    assert owner.get("/api/v1/plantings").json()[0]["cells"] == []


def test_recommendations_without_a_garden_are_empty(owner):  # noqa: F811
    assert owner.get("/api/v1/recommendations").json() == {"garden": False, "now": [], "soon": []}
