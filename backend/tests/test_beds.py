from datetime import UTC, date, datetime, timedelta

from app import external
from app.engine import needs, yearplan
from app.engine.layout import bed_use, footprint_m2
from tests.test_auth_garden import GARDEN
from tests.test_climate import synthetic
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
    planned = owner.post(
        "/api/v1/plantings", json={"crop": "testcrop", "method": "direct", "start_date": str(today + timedelta(days=3))}
    )
    assert planned.json()["status"] == "planned"
    painted = {"crop": "testcrop", "method": "direct", "start_date": str(today), "in_ground": True}
    assert (
        owner.post("/api/v1/plantings", json=painted).json()["status"] == "sown"
    )  # painted today: already in the ground
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


def test_erasing_cells_keeps_the_planting_density(owner):  # noqa: F811
    bed = owner.post("/api/v1/beds", json={"name": "D", "width": 1.2, "length": 1.2}).json()
    made = plant(owner, bed["id"], [[0, 0], [1, 0], [2, 0], [3, 0]], "2026-10-01", quantity=4).json()
    kept = owner.patch(f"/api/v1/plantings/{made['id']}", json={"cells": [[0, 0], [1, 0]]}).json()
    assert kept["quantity"] == 2
    assert not owner.get("/api/v1/beds").json()[0]["over_capacity"]


def test_year_plan_without_beds_is_empty_and_accepting_creates_plantings(owner):  # noqa: F811
    assert owner.get("/api/v1/plan/year").json()["items"] == []
    bed = owner.post("/api/v1/beds", json={"name": "Y", "width": 1.2, "length": 1.2}).json()
    body = {"crop": "testcrop", "method": "direct", "start_date": "2026-12-01", "bed_id": bed["id"], "cells": [[0, 0]]}
    assert owner.post("/api/v1/plan/year", json=[body, body | {"cells": [[1, 0]]}]).json() == {
        "created": 2,
        "replaced": 0,
    }
    assert len(owner.get("/api/v1/plantings").json()) == 2


def test_replanning_replaces_an_unstarted_plan_and_clearing_keeps_hand_made_work(owner):  # noqa: F811
    bed = owner.post("/api/v1/beds", json={"name": "R", "width": 1.2, "length": 1.2}).json()
    body = {"crop": "testcrop", "method": "direct", "start_date": "2026-12-01", "bed_id": bed["id"], "cells": [[0, 0]]}
    mine = owner.post("/api/v1/plantings", json=body | {"cells": [[1, 1]]}).json()
    assert owner.post("/api/v1/plan/year", json=[body]).json() == {"created": 1, "replaced": 0}
    assert owner.get("/api/v1/plan/year").json()["scheduled"] == 1
    assert owner.post("/api/v1/plan/year", json=[body]).json() == {"created": 1, "replaced": 1}
    assert len(owner.get("/api/v1/plantings").json()) == 2  # replaced, not doubled
    assert owner.delete("/api/v1/plan/year").json() == {"removed": 1}
    assert [p["id"] for p in owner.get("/api/v1/plantings").json()] == [mine["id"]]


def test_replan_preview_reports_added_removed_and_moved_before_replacement(owner):  # noqa: F811
    bed = owner.post("/api/v1/beds", json={"name": "Preview", "width": 1.2, "length": 1.2}).json()
    old = {"crop": "testcrop", "method": "direct", "start_date": "2026-12-01", "bed_id": bed["id"], "cells": [[0, 0]]}
    assert owner.post("/api/v1/plan/year", json=[old]).status_code == 201
    proposed = [old | {"cells": [[1, 1]]}, old | {"cells": [[2, 2]], "start_date": "2027-01-01"}]
    response = owner.post("/api/v1/plan/year/preview", json=proposed)
    assert response.status_code == 200
    assert response.json() == {"added": 1, "removed": 0, "moved": 1, "unchanged": 0}
    assert owner.get("/api/v1/plan/year").json()["scheduled"] == 1


def test_companion_planting_exposes_its_purpose(owner):  # noqa: F811
    made = owner.post(
        "/api/v1/plantings",
        json={"crop": "testcrop", "method": "direct", "start_date": "2099-01-01", "in_ground": True},
    )
    assert made.status_code == 201, made.text
    assert made.json()["purpose"] == "food"
    listed = owner.get("/api/v1/plantings").json()
    assert next(p for p in listed if p["id"] == made.json()["id"])["purpose"] == "food"


def test_accepting_successive_plan_uses_the_same_cell_when_dates_do_not_overlap(owner):  # noqa: F811
    bed = owner.post("/api/v1/beds", json={"name": "Succession", "width": 0.6, "length": 0.6}).json()
    body = {"crop": "testcrop", "method": "direct", "bed_id": bed["id"], "cells": [[0, 0]]}
    proposed = [
        body | {"start_date": "2099-01-01", "ends_on": "2099-02-01"},
        body | {"start_date": "2099-03-01", "ends_on": "2099-04-01"},
    ]
    response = owner.post("/api/v1/plan/year", json=proposed)
    assert response.status_code == 201, response.text
    assert response.json()["created"] == 2


def test_accepting_a_plan_rejects_overlapping_or_outside_cells(owner):  # noqa: F811
    bed = owner.post("/api/v1/beds", json={"name": "Strict", "width": 0.6, "length": 0.6}).json()
    body = {"crop": "testcrop", "method": "direct", "start_date": "2099-01-01", "bed_id": bed["id"]}
    overlap = [body | {"cells": [[0, 0]]}, body | {"cells": [[0, 0]]}]
    outside = [body | {"cells": [[2, 2]]}]
    assert owner.post("/api/v1/plan/year", json=overlap).status_code == 422
    assert owner.post("/api/v1/plan/year", json=outside).status_code == 422
    assert owner.get("/api/v1/plantings").json() == []


def test_many_plantings_at_once_all_succeed(owner):  # noqa: F811
    from concurrent.futures import ThreadPoolExecutor

    bed = owner.post("/api/v1/beds", json={"name": "P", "width": 3, "length": 3}).json()
    with ThreadPoolExecutor(8) as pool:
        codes = list(pool.map(lambda i: plant(owner, bed["id"], [[i, 0]], "2026-10-01").status_code, range(12)))
    assert codes == [201] * 12  # job planning is serialised, so no unique-key clash


def test_pantry_orders_by_what_to_use_first_and_defaults_a_best_before(owner):  # noqa: F811
    from datetime import timedelta

    today = datetime.now(UTC).date()
    jar = {"name": "Tomato sauce", "method": "canned", "quantity": 6, "unit": "jars", "made_on": str(today)}
    made = owner.post("/api/v1/pantry", json=jar).json()
    assert made["best_before"] == str(today + timedelta(days=365)) and made["state"] == "ok"
    soon = owner.post(
        "/api/v1/pantry", json=jar | {"name": "Peas", "method": "frozen", "best_before": str(today + timedelta(days=5))}
    )
    assert soon.json()["state"] == "soon"
    assert [i["name"] for i in owner.get("/api/v1/pantry").json()] == ["Peas", "Tomato sauce"]
    assert owner.patch(f"/api/v1/pantry/{made['id']}", json={"quantity": 5}).json()["quantity"] == 5
    assert owner.post("/api/v1/pantry", json=jar | {"quantity": 0}).status_code == 422
    assert owner.delete(f"/api/v1/pantry/{made['id']}").status_code == 204
    assert len(owner.get("/api/v1/pantry").json()) == 1


def test_yield_reads_a_positive_number_and_nothing_else():
    from app.engine.layout import yield_per_m2

    item = lambda v: {"params": {"yield_per_m2": {"value": v, "unit": "kg/m2"}}}  # noqa: E731
    assert yield_per_m2(item(8.0)) == 8.0
    assert yield_per_m2(item(0)) is None
    assert yield_per_m2(item(True)) is None
    assert yield_per_m2(item({"min": 1, "max": 2})) is None
    assert yield_per_m2({}) is None


def test_the_plan_knows_how_many_people_it_feeds_and_how_much_that_is(owner):  # noqa: F811
    assert owner.get("/api/v1/plan/year").json()["people"] == 2
    owner.put("/api/v1/household/settings", json={"people": 6})
    assert owner.get("/api/v1/plan/year").json()["people"] == 6


def test_what_already_grows_is_counted_as_supply_from_its_last_third():
    from app.routers.plan import existing_supply

    class P:  # the few planting fields the helper reads
        def __init__(self, crop, bed_id, cells, status="growing"):
            self.crop, self.bed_id, self.cells, self.status = crop, bed_id, cells, status

    class B:
        cell_cm = 30

    today = date(2026, 10, 10)
    facts = {
        "tomato": {"yield_per_m2": 8.0, "food_group": "fruiting"},
        "mystery": {"yield_per_m2": None, "food_group": None},
    }
    window = lambda p: (date(2026, 9, 10), date(2026, 12, 10))  # noqa: E731  (91 days)
    plantings = [
        P("tomato", 1, [[0, 0], [1, 0]]),
        P("tomato", 1, [], "growing"),
        P("mystery", 1, [[0, 0]]),
        P("tomato", 1, [[0, 0]], "finished"),
    ]
    got = existing_supply(plantings, lambda crop: facts[crop], {1: B()}, window, today)
    assert len(got) == 1  # no cells, no yield and finished plantings add nothing
    group, kg, first, last = got[0]
    assert (group, round(kg, 2), last) == ("fruiting", round(8.0 * 0.09 * 2, 2), date(2026, 12, 10))
    assert first > date(2026, 11, 8)  # the last 30% of the 91 days


class _P:  # a planting with the fields existing_supply reads, for the supply edge cases
    crop, bed_id, cells, status = "tomato", 1, [[0, 0]], "growing"


class _B:
    cell_cm = 30


def test_a_planting_whose_window_is_over_adds_no_supply():
    from app.routers.plan import existing_supply

    facts = {"tomato": {"yield_per_m2": 8.0, "food_group": "fruiting"}}
    past = lambda p: (date(2026, 1, 1), date(2026, 2, 1))  # noqa: E731
    assert existing_supply([_P()], lambda crop: facts[crop], {1: _B()}, past, date(2026, 10, 10)) == []


def test_a_window_beyond_the_year_is_kept_but_adds_nothing_in_year():
    from app.routers.plan import existing_supply

    today = date(2026, 10, 10)
    facts = {"tomato": {"yield_per_m2": 8.0, "food_group": "fruiting"}}
    far = lambda p: (today + timedelta(days=400), today + timedelta(days=500))  # noqa: E731
    existing = existing_supply([_P()], lambda crop: facts[crop], {1: _B()}, far, today)
    assert len(existing) == 1  # it still counts as a planting that grows
    items, supply = yearplan.draft([], {}, [], today, needs.weekly_target(2), existing)
    assert items == [] and all(sum(weeks) == 0 for weeks in supply.values())


def _want(group="leafy", kg=5.0):
    today = date(2026, 10, 10)
    return yearplan.Want(
        "x", "X", "fam", "direct", today, None, today, 60, 1.0, (30, 30),
        today + timedelta(days=60), today + timedelta(days=120), kg, group,
    )  # fmt: skip


def test_the_best_change_is_missing_once_coverage_is_enough():
    from app.routers.plan import ENOUGH, with_coverage

    today = date(2026, 10, 10)
    target = needs.weekly_target(2)
    plenty = [(g, 1000.0, today, today + timedelta(days=364)) for g in needs.GROUPS]  # all year
    grid = [yearplan.Bed(1, "Bed", 8, 12, 30)]
    _, cov = with_coverage(grid, {}, [_want()], today, target, plenty)
    assert cov["overall"] >= ENOUGH and cov["best_change"] is None


def test_no_change_is_suggested_just_under_full_even_when_a_bed_would_add_more(monkeypatch):
    from app.routers import plan

    today = date(2026, 10, 10)
    supply_then = iter([0.96, 0.99])  # coverage with the beds we have, then with an extra bed
    monkeypatch.setattr(plan.yearplan, "draft", lambda *a, **k: ([], {g: [0.0] * needs.WEEKS for g in needs.GROUPS}))
    monkeypatch.setattr(plan.needs, "coverage", lambda target, supply, today: {"overall": next(supply_then)})
    _, cov = plan.with_coverage([], {}, [], today, needs.weekly_target(2), [])
    assert cov["overall"] == 0.96 and cov["best_change"] is None  # 0.96 >= ENOUGH: no change, though 0.03 gain exists


def test_the_best_change_is_missing_when_a_bigger_bed_adds_nothing():
    from app.routers.plan import with_coverage

    today = date(2026, 10, 10)
    _, cov = with_coverage([], {}, [], today, needs.weekly_target(2), [])
    assert cov["overall"] == 0 and cov["best_change"] is None


def test_the_best_change_names_a_four_square_metre_bed_when_it_would_help():
    from app.routers.plan import EXTRA_M2, with_coverage

    today = date(2026, 10, 10)
    items, cov = with_coverage([], {}, [_want()], today, needs.weekly_target(2), [])
    assert items == [] and cov["overall"] == 0  # no bed to plant in yet
    change = cov["best_change"]
    assert change["kind"] == "add_bed_area" and change["m2"] == EXTRA_M2 == 4
    assert change["gain"] >= 0.01


def test_a_crop_without_a_yield_is_listed_as_skipped(owner, monkeypatch):  # noqa: F811
    from app.engine import layout

    monkeypatch.setattr(
        external, "fetch_climate_archive", lambda lat, lon: synthetic(mean=12, amplitude=10, coldest=date(2001, 7, 15))
    )
    owner.put("/api/v1/sites/current", json=GARDEN)
    owner.post("/api/v1/beds", json={"name": "Big", "width": 2.4, "length": 3.6})
    with_yield = owner.get("/api/v1/plan/year").json()
    assert with_yield["skipped_no_yield"] == []
    assert [i["crop"] for i in with_yield["items"]] == ["testcrop"]
    monkeypatch.setattr(layout, "yield_per_m2", lambda item: None)
    without = owner.get("/api/v1/plan/year").json()
    assert without["skipped_no_yield"] == ["testcrop"] and without["items"] == []


def test_the_plan_reports_coverage_and_targets_scale_with_people(owner, monkeypatch):  # noqa: F811
    monkeypatch.setattr(
        external, "fetch_climate_archive", lambda lat, lon: synthetic(mean=14, amplitude=7, coldest=date(2001, 7, 15))
    )
    owner.put("/api/v1/sites/current", json=GARDEN)
    owner.post("/api/v1/beds", json={"name": "Big", "width": 2.4, "length": 3.6})
    two = owner.get("/api/v1/plan/year").json()
    owner.put("/api/v1/household/settings", json={"people": 4})
    four = owner.get("/api/v1/plan/year").json()
    assert two["people"] == 2 and four["people"] == 4
    for group in needs.GROUPS:
        assert two["coverage"]["groups"][group]["target_kg"] == round(needs.weekly_target(2)[group] * needs.WEEKS, 1)
        assert four["coverage"]["groups"][group]["target_kg"] == round(needs.weekly_target(4)[group] * needs.WEEKS, 1)
    assert 0 <= four["coverage"]["overall"] <= 1 and four["skipped_no_yield"] == []


def test_a_drafted_year_plan_can_always_be_accepted_and_replanned(owner, monkeypatch):  # noqa: F811
    from pathlib import Path

    from app import catalog as cat
    from app.main import app
    from tests.e2e_server import fake_archive

    # The real catalog: crops whose days to maturity differ from their catalog cycle exposed a draft/accept mismatch.
    monkeypatch.setattr(app.state, "catalog", cat.load(Path(__file__).resolve().parents[2] / "catalog"))
    monkeypatch.setattr(external, "fetch_climate_archive", fake_archive)
    owner.put("/api/v1/sites/current", json=GARDEN)
    for n, (width, length) in enumerate([(1.2, 2.4), (1.2, 2.4), (1.2, 3.6), (1.2, 2.4)], 1):
        owner.post("/api/v1/beds", json={"name": f"Bed {n}", "width": width, "length": length})
    for _ in range(2):  # the second round replaces the first
        items = owner.get("/api/v1/plan/year").json()["items"]
        assert items
        body = [{k: i[k] for k in ("crop", "method", "start_date", "set_out_date", "bed_id", "cells")} for i in items]
        accepted = owner.post("/api/v1/plan/year", json=body)  # what the app sends: no ends_on
        assert accepted.status_code == 201, accepted.text


def test_cells_are_chosen_so_whole_cells_fit_the_bed(owner):  # noqa: F811
    from app.engine.layout import fit_cell

    assert [fit_cell(*d) for d in ((1.2, 2.4), (2.5, 1.5), (1.3, 2.1), (0.5, 0.5), (1.23, 2.0))] == [30, 25, 10, 25, 30]
    bed = owner.post("/api/v1/beds", json={"name": "Fit", "width": 2.5, "length": 1.5}).json()
    assert bed["cell_cm"] == 25
    made = owner.get("/api/v1/beds").json()[0]
    assert (made["cols"], made["rows"]) == (10, 6)
    owner.post(
        "/api/v1/plantings",
        json={
            "crop": "testcrop",
            "method": "direct",
            "start_date": "2099-01-01",
            "bed_id": bed["id"],
            "cells": [[0, 0]],
        },
    )
    resized = owner.patch(f"/api/v1/beds/{bed['id']}", json={"width": 1.2, "length": 2.4}).json()
    assert resized["cell_cm"] == 30  # the new size is refitted, the planting maps onto it
    assert owner.get("/api/v1/plantings").json()[0]["cells"]
    same = owner.patch(f"/api/v1/beds/{bed['id']}", json={"name": "Renamed"}).json()
    assert same["cell_cm"] == 30
    manual = owner.patch(f"/api/v1/beds/{bed['id']}", json={"cell_cm": 20}).json()
    assert manual["cell_cm"] == 20  # an explicit choice that fits stays


def test_a_beds_cells_follow_the_plants_it_holds(owner, monkeypatch):  # noqa: F811
    from pathlib import Path

    from app import catalog as cat
    from app.main import app

    monkeypatch.setattr(app.state, "catalog", cat.load(Path(__file__).resolve().parents[2] / "catalog"))
    owner.put("/api/v1/sites/current", json=GARDEN)
    bed = owner.post("/api/v1/beds", json={"name": "B", "width": 1.5, "length": 2.5}).json()
    assert bed["cell_cm"] == 25
    url = f"/api/v1/beds/{bed['id']}"
    assert owner.patch(url, json={"for_crop": "beetroot"}).json()["cell_cm"] == 10  # 10 cm spacing: a plant a cell
    made = owner.post(
        "/api/v1/plantings",
        json={
            "crop": "beetroot",
            "method": "direct",
            "start_date": "2026-08-30",
            "bed_id": bed["id"],
            "cells": [[0, 0]],
        },
    )
    assert made.status_code == 201 and made.json()["quantity"] == 1
    wide = owner.patch(url, json={"for_crop": "tomato"}).json()  # a bigger plant never coarsens a bed with small ones
    assert wide["cell_cm"] == 10


def test_a_null_quantity_never_reaches_the_database(owner):  # noqa: F811
    bed = owner.post("/api/v1/beds", json={"name": "Q", "width": 1.2, "length": 1.2}).json()
    made = plant(owner, bed["id"], [[0, 0]], "2026-08-30").json()
    done = owner.patch(f"/api/v1/plantings/{made['id']}", json={"cells": [[0, 0], [1, 0]], "quantity": None})
    assert done.status_code == 200 and done.json()["quantity"] >= 1
