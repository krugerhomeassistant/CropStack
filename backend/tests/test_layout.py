from app.engine.layout import Patch, best_block, dims_cm, patch, plants_in, stagger


def fact(v, unit="cm"):
    return {"value": v, "unit": unit}


def test_the_spacings_of_a_crop_in_cm():
    item = {"params": {"plant_spread": fact(30), "row_spacing": fact(45)}}
    assert dims_cm(item) == (30.0, 45.0)
    assert dims_cm({"params": {"plant_spread": fact(0.5, "m")}}) == (50.0, 50.0)  # no row gap: the spread twice
    assert dims_cm({"params": {"row_spacing": fact(45)}}) is None


def test_a_patch_is_never_tighter_than_the_spacing_and_wastes_the_least_ground():
    assert patch(30, None) == Patch(1, 1, 1)  # unknown spacing: one plant a cell
    assert patch(30, (30, 30)) == Patch(1, 1, 1)
    assert patch(30, (10, 20)) == Patch(1, 1, 3)  # 3 x 1 in a cell
    assert patch(30, (5, 5)).per == 16  # capped
    assert patch(30, (45, 45)) == Patch(2, 2, 1)  # 45 cm needs two 30 cm cells each way, not 2.25 cells
    assert patch(30, (20, 45)).cells == 2 and sorted((patch(30, (90, 150)).w, patch(30, (90, 150)).h)) == [3, 5]
    assert patch(10, (45, 45)) == Patch(5, 5, 1)  # finer cells follow the spacing more closely


def test_plants_in_a_block_of_cells():
    assert plants_in(30, (45, 45), 8) == 2 and plants_in(30, (45, 45), 3) == 1  # whole patches, at least one
    assert plants_in(30, (30, 30), 5) == 5 and plants_in(30, (10, 10), 2) == 18 and plants_in(30, None, 4) == 4


def test_a_block_is_a_solid_rectangle_of_whole_patches_on_free_cells():
    free = {(c, r) for c in range(4) for r in range(3)}
    cells, count = best_block(4, 3, free, Patch(2, 2, 1), 2)  # two patches: 4 x 2 cells fit
    assert count == 2 and len(cells) == 8
    free -= {(2, 1)}  # a busy cell in the middle: only one 2 x 2 patch still fits
    cells, count = best_block(4, 3, free, Patch(2, 2, 1), 2)
    assert count == 1 and len(cells) == 4 and (2, 1) not in cells
    assert best_block(2, 2, {(0, 0), (1, 1)}, Patch(2, 2, 1), 1) is None


def test_the_key_chooses_among_the_places_a_block_fits():
    free = {(c, r) for c in range(6) for r in range(4)}
    first = best_block(6, 4, free, Patch(1, 1, 1), 2)[0]
    assert len(first) == 2 and (0, 0) in first  # no preference: the top-left corner
    far = best_block(6, 4, free, Patch(1, 1, 1), 2, key=lambda cells: (-max(c for c, _ in cells),))[0]
    assert max(c for c, _ in far) == 5


def test_a_solid_block_can_be_offset_into_brick_rows_on_the_same_free_ground():
    free = {(c, r) for c in range(12) for r in range(8)}
    p = Patch(2, 2, 1)
    solid, _ = best_block(12, 8, free, p, 4)  # 2 x 2 patches, 4 x 4 cells
    out = stagger(solid, 12, 8, free, p)
    assert len(out) == 16 and len(set(out)) == 16 and set(out) <= free  # same count, no overlap
    first = min(c for c, r in out if r in (0, 1))
    second = min(c for c, r in out if r in (2, 3))
    assert abs(first - second) == 1  # the second row of patches is moved half a patch


def test_no_offset_when_there_is_nothing_to_shift_or_no_room():
    assert stagger([(0, 0), (0, 1)], 6, 6, {(c, r) for c in range(6) for r in range(6)}, Patch(1, 1, 4)) is None
    p = Patch(2, 2, 1)
    tight = {(c, r) for c in range(4) for r in range(4)}
    assert stagger(best_block(4, 4, tight, p, 4)[0], 4, 4, tight, p) is None  # no spare width for the moved row
    strip = {(c, r) for c in range(8) for r in range(2)}
    assert stagger(best_block(8, 2, strip, p, 4)[0], 8, 2, strip, p) is None  # one row of patches: nothing to offset
