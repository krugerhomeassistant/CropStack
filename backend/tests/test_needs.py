from datetime import date, timedelta

from app.engine import needs

TODAY = date(2026, 10, 10)


def test_targets_scale_with_people_and_the_shares_cover_the_basket():
    assert abs(sum(needs.GROUP_SHARE.values()) - 1) < 1e-9
    one, four = needs.weekly_target(1), needs.weekly_target(4)
    assert all(abs(four[g] - 4 * one[g]) < 1e-9 for g in needs.GROUPS)
    assert abs(sum(one.values()) - 2.8) < 1e-9  # 0.4 kg a day for a week


def test_a_harvest_is_spread_evenly_over_its_weeks():
    got = needs.spread(TODAY, TODAY + timedelta(days=14), TODAY + timedelta(days=27), 4.0)
    assert got == {2: 2.0, 3: 2.0}


def test_a_harvest_is_clipped_to_the_year_and_the_past_counts_for_nothing():
    late = needs.spread(TODAY, TODAY + timedelta(days=357), TODAY + timedelta(days=400), 7.0)
    assert late == {51: 1.0}  # seven weeks of harvest, one of them inside the year
    assert needs.spread(TODAY, TODAY - timedelta(days=30), TODAY - timedelta(days=1), 5.0) == {}
    assert sum(late.values()) < 7.0  # the part of the harvest past the year is not counted


def test_an_unaligned_short_harvest_adds_up_to_its_kilograms():
    got = needs.spread(TODAY, TODAY + timedelta(days=3), TODAY + timedelta(days=9), 4.0)
    assert got == {0: 2.0, 1: 2.0}  # touches two today-aligned weeks, so it is split over both
    assert abs(sum(got.values()) - 4.0) < 1e-9


def test_coverage_counts_each_week_only_up_to_its_target():
    target = {g: 1.0 for g in needs.GROUPS}
    supply = {g: [0.0] * needs.WEEKS for g in needs.GROUPS}
    supply["leafy"] = [3.0] * 26 + [0.0] * 26  # a glut, then nothing: the glut does not cover the gap
    cov = needs.coverage(target, supply, TODAY)
    assert cov["groups"]["leafy"]["covered"] == 0.5
    assert cov["groups"]["leafy"]["weeks_short"][0] == (TODAY + timedelta(weeks=26)).isoformat()
    assert cov["groups"]["herb"]["covered"] == 0.0
    assert cov["overall"] == 0.1  # leafy is a fifth of the basket, half covered
