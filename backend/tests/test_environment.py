import math
from datetime import date, timedelta

import pytest

from app import environment as env

START, END = date(1995, 1, 1), date(2025, 1, 1)  # 30 complete years


def make(
    tmin_of=lambda d: 10.0,
    tmax_of=lambda d: 22.0,
    precip_of=lambda d: 1.0,
    et0_of=lambda d: 4.0,
    half_life: float = 10.0,
) -> env.Climatology:
    days = [START + timedelta(days=i) for i in range((END - START).days)]
    return env.build(
        days,
        {
            "tmin": [tmin_of(d) for d in days],
            "tmax": [tmax_of(d) for d in days],
            "precip": [precip_of(d) for d in days],
            "et0": [et0_of(d) for d in days],
        },
        half_life=half_life,
    )


def seasonal(mean: float, amplitude: float, coldest_doy: int):
    """Cosine annual cycle; coldest on coldest_doy."""
    return lambda d: mean - amplitude * math.cos(2 * math.pi * (env.doy(d) - coldest_doy) / 365)


def test_build_years_weights_and_leap_days():
    c = make()
    assert c.years == list(range(1995, 2025))
    assert all(len(v) == 365 for v in c.series["tmin"])
    assert sum(c.weights) == pytest.approx(1.0)
    assert c.weights == sorted(c.weights)  # recent years weigh more
    assert c.weights[-1] / c.weights[-11] == pytest.approx(2.0)  # half-life 10 years
    assert c.trends == {}  # flat temperatures: no trend


def test_partial_years_are_dropped():
    days = [date(2020, 6, 1) + timedelta(days=i) for i in range(365 + 214)]  # Jun 2020 .. Dec 2021
    c = env.build(days, {"tmin": [5.0] * len(days)})
    assert c.years == [2021]


def test_window_probability_follows_the_seasons():
    c = make(tmin_of=seasonal(5, 10, coldest_doy=15))  # northern-style: coldest mid-January
    assert env.prob_any(c, "tmin", "le", 0, start_doy=1, days=31) == pytest.approx(1.0)
    assert env.prob_any(c, "tmin", "le", 0, start_doy=182, days=31) == 0.0


def test_new_cold_tail_appears_without_configuration():
    """AC-P2: frost risk exists exactly when the data contains it; no setting, mode or region involved."""
    mild = seasonal(12, 4, coldest_doy=196)  # never below 8 °C
    assert env.prob_any(make(tmin_of=mild), "tmin", "le", 0, 182, 30) == 0.0

    def cold_snaps(d):  # three years in ten get a cold July week
        return mild(d) - (12 if d.year % 10 < 3 and d.month == 7 and 10 <= d.day <= 16 else 0)

    c = make(tmin_of=cold_snaps)
    expected = sum(w for y, w in zip(c.years, c.weights, strict=True) if y % 10 < 3)
    assert env.prob_any(c, "tmin", "le", 0, 182, 30) == pytest.approx(expected)
    assert 0.2 < expected < 0.4


def test_hemisphere_mirror_shifts_everything_by_half_a_year():
    """AC-P3: the same climate six months apart gives the same answers six months apart."""
    north = make(tmin_of=seasonal(4, 9, coldest_doy=15))
    south = make(tmin_of=seasonal(4, 9, coldest_doy=15 + 182))
    n_curve = env.daily_prob(north, "tmin", "le", 0)
    s_curve = env.daily_prob(south, "tmin", "le", 0)
    for day in range(1, 366):
        assert s_curve[(day - 1 + 182) % 365] == pytest.approx(n_curve[day - 1], abs=0.04)


def test_window_crossing_new_year_uses_the_following_year():
    c = make(precip_of=lambda d: float(d.year))  # value = its calendar year (rain is never trend-adjusted)
    pairs = env.windows(c, "precip", start_doy=355, days=20)  # 21 Dec .. 9 Jan
    assert len(pairs) == 29  # the last year has no following January
    first_values, _ = pairs[0]
    assert first_values[0] == 1995 and first_values[-1] == 1996
    assert sum(w for _, w in pairs) == pytest.approx(1.0)


def test_recent_years_count_more():
    c = make(precip_of=lambda d: 4.0 if d.year >= 2015 else 2.0)  # wetter last decade (not trend-adjusted)
    mean = env.summary(env.per_year(c, "precip", 1, 365, lambda v: sum(x or 0 for x in v)))["mean"]
    unweighted = (20 * 730 + 10 * 1460) / 30
    assert unweighted < mean < 1460


def test_significant_warming_is_removed_but_noise_is_not():
    warming = make(tmin_of=lambda d: 8 + 0.05 * (d.year - 1995) + math.sin(d.toordinal()))
    assert warming.trends["tmin"] == pytest.approx(0.05, abs=0.005)
    # 1995 is lifted to the 2025 level, so the oldest year no longer drags the estimate down.
    assert env._mean(warming.series["tmin"][0]) == pytest.approx(env._mean(warming.series["tmin"][-1]), abs=0.05)

    noisy = make(tmin_of=lambda d: 8 + (0.6 if (d.year * 7919) % 3 == 0 else -0.3))  # no trend, just jumps
    assert "tmin" not in noisy.trends


def test_weighted_quantile():
    pairs = [(1.0, 1), (2.0, 1), (3.0, 1), (4.0, 1)]
    assert env.weighted_quantile(pairs, 0.5) == pytest.approx(2.5)
    assert env.weighted_quantile(pairs, 0.0) == 1.0 and env.weighted_quantile(pairs, 1.0) == 4.0
    assert env.weighted_quantile([(1.0, 3), (10.0, 1)], 0.5) == pytest.approx(1.0)  # heavy weight wins


def test_growing_degree_days():
    assert env.gdd_day(10, 20, base=10) == 5
    assert env.gdd_day(20, 40, base=10, cutoff=30) == 15  # max capped at the cutoff
    assert env.gdd_day(2, 8, base=10) == 0
    c = make(tmin_of=lambda d: 10.0, tmax_of=lambda d: 20.0)  # 5 GDD a day above base 10
    assert {v for v, _ in env.days_to_gdd(c, 60, target=100, base=10)} == {20.0}
    never = env.days_to_gdd(make(tmin_of=lambda d: 2.0, tmax_of=lambda d: 8.0), 60, target=100, base=10)
    assert all(math.isinf(v) for v, _ in never)  # too cold to ever mature: visible as a probability


def test_water_deficit():
    c = make(precip_of=lambda d: 2.0, et0_of=lambda d: 5.0)
    assert {round(v, 6) for v, _ in env.water_deficit(c, 10, days=10, kc=1.0)} == {30.0}
    wet = make(precip_of=lambda d: 9.0, et0_of=lambda d: 5.0)
    assert {v for v, _ in env.water_deficit(wet, 10, days=10, kc=1.0)} == {0.0}


def test_daily_quantile_bands_are_ordered():
    c = make(tmin_of=lambda d: 5 + (d.year % 7))
    for lo, mid, hi in env.daily_quantiles(c, "tmin"):
        assert lo <= mid <= hi


def test_bad_queries_are_rejected():
    c = make()
    with pytest.raises(ValueError):
        env.prob_any(c, "tmin", "eq", 0, 1, 10)
    with pytest.raises(ValueError):
        env.windows(c, "tmin", 0, 10)
