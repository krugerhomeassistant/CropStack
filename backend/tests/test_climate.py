import math
from datetime import date, timedelta

import pytest

from app import climate


def synthetic(
    mean: float,
    amplitude: float,
    coldest: date,
    years: int = 30,
    year_shift: float = 0.0,
    day_range: float = 12.0,
    rain_cold: float = 1.0,
    rain_warm: float = 1.0,
) -> dict:
    """Fake Open-Meteo archive: a cosine annual cycle of daily minimum temperature.

    year_shift spreads the years apart (°C) so frost dates differ between years; day_range = max - min;
    rain_cold / rain_warm = mm per day in the colder / warmer half of the year.
    """
    # Like the real fetch: the last `years` complete calendar years before today.
    start = date(date.today().year - years, 1, 1)
    days = [start + timedelta(days=i) for i in range((date(date.today().year, 1, 1) - start).days)]
    cold = coldest.timetuple().tm_yday
    # -cos(...) = -1 on the coldest day: tmin = mean - amplitude there
    cycle = [-math.cos(2 * math.pi * (d.timetuple().tm_yday - cold) / 365) for d in days]
    tmin = [mean + year_shift * ((d.year % 10) - 4.5) / 4.5 + amplitude * c for d, c in zip(days, cycle, strict=True)]
    return {
        "elevation": 1339.0,
        "timezone": "Africa/Johannesburg",
        "daily": {
            "time": [d.isoformat() for d in days],
            "temperature_2m_min": tmin,
            "temperature_2m_max": [t + day_range for t in tmin],
            "soil_temperature_0_to_7cm_mean": [t + 6 for t in tmin],
            "precipitation_sum": [rain_cold if c < 0 else rain_warm for c in cycle],
            "et0_fao_evapotranspiration": [max(0.5, 3 + 0.2 * t) for t in tmin],
            "relative_humidity_2m_mean": [70.0 for _ in tmin],
            "wind_speed_10m_max": [15.0 for _ in tmin],
        },
    }


def days_between(a: str, b: str) -> int:
    return (date.fromisoformat(f"2001-{b}") - date.fromisoformat(f"2001-{a}")).days


def test_northern_hemisphere_frost_window():
    summary = climate.summarize(synthetic(mean=5, amplitude=10, coldest=date(2001, 1, 15)))
    report = climate.report(summary, latitude=45, frost_probability=50)
    # tmin <= 0 when the cosine term <= -0.5, i.e. within ~61 days of the coldest day
    assert abs(days_between("03-16", report["last_spring_frost"])) <= 2
    assert abs(days_between("11-15", report["first_fall_frost"])) <= 2
    assert 240 <= report["growing_season_days"] <= 246
    assert report["frost_years_pct"] == 100 and not report["frost_free"]
    assert summary["period"] == f"{date.today().year - 30}-{date.today().year - 1}"
    assert len(summary["last_frost"]) == 29  # partial first and last seasons dropped


def test_southern_hemisphere_is_mirrored():
    summary = climate.summarize(synthetic(mean=5, amplitude=10, coldest=date(2001, 7, 15)))
    report = climate.report(summary, latitude=-26, frost_probability=50)
    assert abs(days_between("09-14", report["last_spring_frost"])) <= 2
    assert abs(days_between("05-15", report["first_fall_frost"])) <= 2
    assert 240 <= report["growing_season_days"] <= 246


def test_risk_level_moves_dates_the_right_way():
    summary = climate.summarize(synthetic(mean=5, amplitude=10, coldest=date(2001, 1, 15), year_shift=3))
    cautious, typical, bold = (climate.frost_dates(summary, p) for p in (10, 50, 90))
    # A lower accepted risk means a later spring date and an earlier fall date.
    assert cautious["last_spring_frost"] > typical["last_spring_frost"] > bold["last_spring_frost"]
    assert cautious["first_fall_frost"] < typical["first_fall_frost"] < bold["first_fall_frost"]
    assert cautious["growing_season_days"] < typical["growing_season_days"] < bold["growing_season_days"]


def test_frost_free_climate():
    report = climate.report(climate.summarize(synthetic(mean=20, amplitude=3, coldest=date(2001, 7, 15))), 1.3, 50)
    assert report["frost_free"]
    assert report["last_spring_frost"] is None and report["first_fall_frost"] is None
    assert report["growing_season_days"] == 365


def test_rare_frost_is_hidden_at_bold_risk_but_shown_when_cautious():
    # Mild climate where only the colder half of the years reach frost.
    summary = climate.summarize(synthetic(mean=10, amplitude=9.4, coldest=date(2001, 7, 15), year_shift=1))
    assert 0 < climate.frost_dates(summary, 50)["frost_years_pct"] < 100
    assert climate.frost_dates(summary, 10)["last_spring_frost"] is not None
    assert climate.frost_dates(summary, 90)["last_spring_frost"] is None


@pytest.mark.parametrize(
    ("min_c", "zone"),
    [(-17.0, "7a"), (-20.6, "6a"), (-12.22, "8a"), (-8.0, "8b"), (-51.1, "1a"), (-60, "1a"), (40, "13b")],
)
def test_hardiness_zone(min_c, zone):
    assert climate.hardiness_zone([min_c])["zone"] == zone


def test_day_length():
    equator = climate.monthly_daylight(0)
    assert all(12.0 <= h <= 12.3 for h in equator)
    june = climate.day_length_hours(60, 172)
    assert 18.5 <= june <= 19.0
    assert 5.6 <= climate.day_length_hours(-60, 172) <= 6.1  # refraction lengthens both: sum ~24.7 h
    assert climate.day_length_hours(70, 172) == 24.0  # midnight sun


def test_monthly_means_skip_missing_values():
    days = [date(2020, 1, 1), date(2020, 1, 2), date(2020, 2, 1)]
    assert climate.monthly_means(days, [1.0, None, 4.0])[:3] == [1.0, 4.0, None]


def test_mediterranean_climate_western_cape_like():
    """Mild wet winters, hot dry summers: described from the data, no climate label involved."""
    raw = synthetic(mean=11, amplitude=5, coldest=date(2001, 7, 15), day_range=15, rain_cold=2.5, rain_warm=0.3)
    report = climate.report(climate.summarize(raw), latitude=-33.9, frost_probability=50)
    assert report["frost_free"] and report["frost_nights_per_year"] == 0
    assert 480 <= report["annual_rain_mm"] <= 540
    season = report["rain_season"]
    assert season["start_month"] in (4, 5) and season["share_pct"] > 80  # most rain ~Apr/May-Sep/Oct
    assert report["hottest_day_c"] == pytest.approx(31, abs=0.5)  # mean 11 + amplitude 5 + range 15


def test_frosty_climate_counts_frost_nights_by_month():
    report = climate.report(climate.summarize(synthetic(mean=3, amplitude=10, coldest=date(2001, 1, 15))), 50, 50)
    nights = report["monthly"]["frost_nights"]
    assert nights[0] > 25 and nights[6] == 0  # nearly every January night, never in July
    assert report["frost_nights_per_year"] == pytest.approx(sum(nights), abs=0.5)


def test_rain_season_wraps_the_year_and_handles_dry_places():
    summer_rain = [100, 90, 80, 40, 10, 5, 5, 5, 20, 50, 80, 100]
    assert climate.rain_season(summer_rain) == {"start_month": 10, "end_month": 3, "share_pct": 85}
    assert climate.rain_season([50] * 12)["share_pct"] == 50
    assert climate.rain_season([0] * 12) is None


def test_significant_trend_is_reported_per_decade():
    report = climate.report(climate.summarize(synthetic(5, 10, date(2001, 1, 15))), 50, 50, {"tmin": 0.031})
    assert report["trend_per_decade"] == {"tmin": 0.31}


def test_monthly_totals_average_per_year():
    days = [date(2020, 1, 1), date(2020, 1, 2), date(2021, 1, 1)]
    assert climate.monthly_totals(days, [2.0, 3.0, 5.0])[0] == 5.0  # (2 + 3 + 5) mm over 2 Januaries
