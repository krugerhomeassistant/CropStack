from datetime import date

from app.engine import layout, recommend

W = {
    "start": "09-20",
    "end": "11-10",
    "best_start": "10-01",
    "best_end": "10-20",
    "all_year": False,
    "success": 0.9,
    "days_to_maturity": {"p50": 60},
}


def test_a_window_is_now_when_today_is_inside_it_and_soon_when_it_is_near():
    now = recommend.timing(W, date(2026, 10, 10), 21)
    assert now["state"] == "now" and now["until"] == date(2026, 11, 10) and now["best_to"] == date(2026, 10, 20)
    soon = recommend.timing(W, date(2026, 9, 1), 21)
    assert soon["state"] == "soon" and soon["start"] == date(2026, 9, 20)
    assert recommend.timing(W, date(2026, 8, 1), 21) is None
    assert recommend.timing(W, date(2026, 11, 20), 21) is None  # over: the next one is ten months away


def test_a_window_that_crosses_new_year_is_now_in_january():
    w = W | {"start": "11-15", "end": "02-10", "best_start": "12-01", "best_end": "01-10"}
    t = recommend.timing(w, date(2027, 1, 5), 21)
    assert t["state"] == "now" and t["until"] == date(2027, 2, 10)


def test_best_option_prefers_what_is_open_now():
    now = {"state": "now", "start": date(2026, 10, 10), "success": 0.7, "method": "transplant"}
    soon = {"state": "soon", "start": date(2026, 10, 15), "success": 0.99, "method": "direct"}
    assert recommend.best_option([soon, now]) is now and recommend.best_option([]) is None


def test_cells_cover_the_bed_and_hold_a_crop_only_while_it_grows():
    assert layout.grid(1.2, 2.4, 30) == (4, 8) and layout.grid(0.5, 0.5, 30) == (2, 2)
    assert layout.per_cell(30, 0.09) == 1 and layout.per_cell(30, 0.0025) == 16 and layout.per_cell(30, None) == 1
    a, b = layout.occupancy(date(2026, 10, 1), None, None, "sown", 60, date(2026, 10, 10))
    assert (a, b) == (date(2026, 10, 1), date(2026, 11, 30))
    _, over = layout.occupancy(date(2026, 10, 1), None, None, "finished", 60, date(2026, 10, 10))
    assert over == date(2026, 10, 10)  # finished: cells free from today


def test_free_cells_and_clashes_look_at_dates():
    held = [((0, 0), date(2026, 10, 1), date(2026, 11, 30))]
    free = layout.free_cells(2, 1, held, date(2026, 12, 1), date(2027, 1, 31))
    assert free == [(0, 0), (1, 0)]  # the cell is free again after the first crop
    assert layout.free_cells(2, 1, held, date(2026, 11, 1), date(2026, 12, 31)) == [(1, 0)]
    both = [(1, (0, 0), date(2026, 10, 1), date(2026, 11, 30)), (2, (0, 0), date(2026, 11, 15), date(2027, 1, 1))]
    assert layout.clashes(both) == [((0, 0), 1, 2)]
    assert layout.clashes([both[0], (2, (0, 0), date(2026, 12, 1), date(2027, 1, 1))]) == []
