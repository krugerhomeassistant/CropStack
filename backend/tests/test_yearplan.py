from datetime import date, timedelta

from app.engine import needs
from app.engine.yearplan import Bed, Want, draft

TODAY = date(2026, 10, 10)
CROPS = {  # crop: (food group, kg per m2 per cycle, days in the ground)
    "lettuce": ("leafy", 3.0, 60),
    "tomato": ("fruiting", 8.0, 120),
    "carrot": ("root", 4.0, 90),
    "kale": ("brassica", 3.0, 100),
    "pea": ("legume", 1.2, 80),
    "zucchini": ("squash", 8.0, 80),
    "onion": ("allium", 3.0, 120),
    "basil": ("herb", 1.0, 60),
}


def want(crop, group, planted, kg=4.0, family="", days=60):
    harvest = planted + timedelta(days=days - 20)
    return Want(
        crop, crop, family, "direct", planted, None, planted, days, 0.9, None,
        harvest, harvest + timedelta(days=21), kg, group,
    )  # fmt: skip


YEAR = [want(c, g, TODAY + timedelta(days=30 * m), kg, days=d) for m in range(12) for c, (g, kg, d) in CROPS.items()]


def cells(items):
    return sum(len(i["cells"]) for i in items)


def run(people, beds, taken=None, wants=YEAR, existing=()):
    grid = [Bed(i, f"B{i}", 12, 8, 30) for i in range(1, beds + 1)]
    return draft(grid, taken or {}, wants, TODAY, needs.weekly_target(people), list(existing))


def test_more_people_plant_more_until_the_target_is_met():
    assert cells(run(4, 3)[0]) > cells(run(1, 3)[0])
    assert cells(run(1, 3)[0]) == cells(run(1, 8)[0])  # a household of one is fed: more ground adds nothing


def test_nothing_is_double_booked_and_the_draft_is_repeatable():
    items, _ = run(2, 2)
    assert items == run(2, 2)[0]
    for bed in (1, 2):
        held = [
            (tuple(c), i["set_out_date"] or i["start_date"], i["until"])
            for i in items
            if i["bed_id"] == bed
            for c in i["cells"]
        ]
        for n, (cell, a, z) in enumerate(held):
            assert not any(cell == c and a <= y and b <= z for c, b, y in held[n + 1 :])


def test_cells_that_held_the_same_family_come_last_so_crops_rotate():
    one_tomato = [want("tomato", "fruiting", TODAY, kg=8.0, family="Solanaceae")]
    every_cell = [((c, r), date(2026, 5, 1), date(2026, 10, 1), "Solanaceae") for c in range(12) for r in range(8)]
    assert {i["bed_id"] for i in run(4, 2, wants=one_tomato)[0]} == {1}
    assert {i["bed_id"] for i in run(4, 2, {1: every_cell}, one_tomato)[0]} == {2}


def test_a_crop_with_no_yield_or_group_is_left_out():
    bare = [want("mystery", None, TODAY, kg=None), want("nogroup", None, TODAY)]
    assert run(4, 1, wants=bare)[0] == []


def test_what_already_grows_counts_toward_the_target():
    glut = [("fruiting", 5000.0, TODAY, TODAY + timedelta(days=360))]
    items, supply = run(4, 3, existing=glut)
    assert not [i for i in items if i["food_group"] == "fruiting"]
    assert supply["fruiting"][10] > 0


def test_harvests_outside_the_year_are_ignored():
    gone = [
        want("lettuce", "leafy", TODAY - timedelta(days=200)),
        want("kale", "brassica", TODAY + timedelta(days=500)),
    ]
    assert run(4, 1, wants=gone)[0] == []
