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


def test_draft_never_overlaps_cells_across_generated_items():
    items, _ = run(8, 2)
    for bed_id in {i["bed_id"] for i in items}:
        rows = [i for i in items if i["bed_id"] == bed_id]
        for n, left in enumerate(rows):
            left_cells = {tuple(c) for c in left["cells"]}
            left_start = left["set_out_date"] or left["start_date"]
            for right in rows[n + 1 :]:
                right_cells = left_cells & {tuple(c) for c in right["cells"]}
                right_start = right["set_out_date"] or right["start_date"]
                overlap = left_start <= right["until"] and right_start <= left["until"]
                assert not (right_cells and overlap), (bed_id, left, right)


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


def sized(crop, group, planted, dims, kg=8.0):
    w = want(crop, group, planted, kg=kg)
    return Want(*[*w.__dict__.values()][:9], dims, *[*w.__dict__.values()][10:])


def grows(crop, cells, a=TODAY - timedelta(days=30), z=TODAY + timedelta(days=200)):
    """Cells already held by a planting that stays, as `taken` wants them."""
    return [(tuple(c), a, z, "", crop) for c in cells]


def test_a_big_plant_takes_whole_patches_of_the_ground_its_spacing_needs():
    # 60 cm plants on 30 cm cells: a 2 x 2 patch each, in whole patches
    items, _ = run(4, 1, wants=[sized("zucchini", "squash", TODAY, (60, 60))])
    assert items
    for i in items:
        assert i["patch"] == [2, 2] and i["cells_per_plant"] == 4 and len(i["cells"]) % 4 == 0
        assert i["plants"] == len(i["cells"]) // 4
    # a plant wider one way than the other needs a patch that long: 20 x 45 cm is 1 x 2 or 2 x 1 cells
    odd, _ = run(4, 1, wants=[sized("bean", "legume", TODAY, (20, 45))])
    assert odd and all(i["patch"] in ([1, 2], [2, 1]) for i in odd)
    # small plants still go several to a cell, as many as fit at their spacing in both directions
    small, _ = run(4, 1, wants=[sized("lettuce", "leafy", TODAY, (10, 10), kg=3.0)])
    assert small and small[0]["cells_per_plant"] == 1 and small[0]["plants"] == 9 * len(small[0]["cells"])


def test_several_big_plants_are_staggered_in_offset_rows_not_one_solid_block():
    items, _ = run(4, 1, wants=[sized("zucchini", "squash", TODAY, (60, 60))])
    blocks = [i for i in items if len(i["cells"]) >= 8]  # at least two rows of 2 x 2 patches
    assert blocks
    for i in blocks:
        cells = {tuple(c) for c in i["cells"]}
        starts = {
            min(c for c, r in cells if r in (y, y + 1))
            for y in {min(r for _, r in cells), max(r for _, r in cells) - 1}
        }
        assert len(starts) > 1  # the rows of patches do not all begin in the same column
        assert i["plants"] == len(cells) // 4 and i["patch"] == [2, 2]


GOOD = {"tomato": {"basil", "marigold"}, "basil": {"tomato"}, "marigold": {"tomato"}}
AVOID = {"tomato": {"fennel"}, "fennel": {"tomato"}}
TOMATO = [sized("tomato", "fruiting", TODAY, (45, 45))]
BASIL_BLOCK = [(6, 3), (7, 3), (6, 4), (7, 4)]


def edge(cells, others):
    return {(c + dc, r + dr) for c, r in cells for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))} & set(others)


def test_a_crop_is_placed_touching_its_good_companion():
    grid = [Bed(1, "B1", 12, 8, 30)]
    taken = {1: grows("basil", BASIL_BLOCK)}
    alone, _ = draft(grid, taken, TOMATO, TODAY, needs.weekly_target(2), [])
    assert not edge({tuple(c) for c in alone[0]["cells"]}, BASIL_BLOCK)  # nothing draws it there
    items, _ = draft(grid, taken, TOMATO, TODAY, needs.weekly_target(2), [], {"good": GOOD})
    cells = {tuple(c) for c in items[0]["cells"]}
    assert edge(cells, BASIL_BLOCK) and not cells & set(BASIL_BLOCK)
    assert items[0]["pairs_with"] == ["Basil"]


def test_a_crop_stays_out_of_a_bed_with_a_bad_neighbour():
    grid = [Bed(i, f"B{i}", 12, 8, 30) for i in (1, 2)]
    taken = {1: grows("fennel", [(0, 0)])}
    items, _ = draft(grid, taken, TOMATO, TODAY, needs.weekly_target(2), [], {"avoid": AVOID})
    assert items and {i["bed_id"] for i in items} == {2}
    # a bad neighbour that is gone by sowing time is no obstacle
    gone = {1: grows("fennel", [(0, 0)], TODAY - timedelta(days=200), TODAY - timedelta(days=100))}
    items, _ = draft(grid, gone, TOMATO, TODAY, needs.weekly_target(2), [], {"avoid": AVOID})
    assert {i["bed_id"] for i in items} == {1}


def test_a_companion_flower_stands_touching_the_crop_and_on_the_edge_of_the_bed():
    flowers = {"tomato": ["marigold"]}
    marigold = sized("marigold", None, TODAY + timedelta(days=10), (30, 30), kg=None)
    grid = [Bed(1, "B1", 12, 8, 30)]
    items, _ = draft(
        grid, {}, [*TOMATO, marigold], TODAY, needs.weekly_target(2), [], {"good": GOOD, "flowers": flowers}
    )
    tomato = next(i for i in items if i["crop"] == "tomato")
    flower = next(i for i in items if i["crop"] == "marigold")
    t, f = {tuple(c) for c in tomato["cells"]}, {tuple(c) for c in flower["cells"]}
    assert flower["bed_id"] == tomato["bed_id"] and flower["companion_for"] == ["tomato"]
    assert len(f) == 2 and not t & f and edge(t, f)  # two cells, touching the tomatoes
    assert flower["food_group"] is None and flower["kg"] == 0
    assert tomato["flowers"] == ["marigold"] and tomato["flower_hints"] == [] and "Marigold" not in tomato["pairs_with"]
    # without the flower among the wants the crop only gets the traditional hint
    items, _ = draft(grid, {}, TOMATO, TODAY, needs.weekly_target(2), [], {"flowers": flowers})
    assert [i["crop"] for i in items] == ["tomato"] and items[0]["flower_hints"] == ["Marigold"]


def test_one_flower_stand_serves_every_crop_in_the_bed_that_wants_it():
    flowers = {"tomato": ["marigold"], "carrot": ["marigold"]}
    both = [sized("tomato", "fruiting", TODAY, (45, 45)), want("carrot", "root", TODAY, kg=4.0, days=90)]
    marigold = sized("marigold", None, TODAY + timedelta(days=5), (30, 30), kg=None)
    items, _ = draft(
        [Bed(1, "B1", 12, 8, 30)], {}, [*both, marigold], TODAY, needs.weekly_target(4), [], {"flowers": flowers}
    )
    blocks = [i for i in items if i["crop"] == "marigold"]
    assert len(blocks) == 1 and blocks[0]["companion_for"] == ["carrot", "tomato"]
