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
