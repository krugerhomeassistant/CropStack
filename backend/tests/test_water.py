from datetime import date, timedelta

from app.engine.water import WaterProfile, depletion_path, first_dry_day, profile_from_item

# Kc 0.5 / 1.0 / 0.8 over 10 + 10 + 20 + 10 days; roots 0.2 m growing to 0.6 m; p = 0.5
W = WaterProfile((0.5, 1.0, 0.8), (10, 10, 20, 10), 0.6, 0.5)
SOWN = date(2026, 10, 1)


def week(et0: float, rain: float = 0.0, start: date = SOWN, n: int = 7) -> list[dict]:
    return [{"date": str(start + timedelta(days=i)), "et0": et0, "precip": rain} for i in range(1, n + 1)]


def test_kc_and_roots_follow_the_stages():
    assert [W.kc_at(a) for a in (0, 10, 15, 20, 30, 40, 50)] == [0.5, 0.5, 0.75, 1.0, 1.0, 1.0, 0.8]
    assert W.root_at(0) == 0.2 and abs(W.root_at(10) - 0.4) < 1e-9 and W.root_at(40) == 0.6


def test_depletion_is_hand_computable():
    # Kc 0.5, ET0 10 mm → 5 mm a day. Day n: roots 0.2 + 0.02n m, so RAW = 0.5 * 120 * (0.2 + 0.02n) = 12 + 1.2n.
    path = depletion_path(W, SOWN, SOWN, week(10.0))
    assert [round(r["depletion"]) for r in path] == [5, 10, 15, 20, 25, 30, 35]
    assert round(path[0]["raw"], 1) == 13.2
    assert first_dry_day(path, SOWN + timedelta(days=1))["date"] == SOWN + timedelta(days=4)  # 20 mm >= 16.8 mm
    assert first_dry_day(path, SOWN + timedelta(days=1), horizon=2) is None  # day 3: 15 mm < 15.6 mm


def test_rain_refills_and_watering_resets():
    rainy = depletion_path(W, SOWN, SOWN, week(4.0, rain=10.0))  # 8 mm of 10 counts, more than the 2 mm used
    assert all(r["depletion"] == 0 for r in rainy)
    # watered on day 3: counting starts from a full soil on that day
    later = depletion_path(W, SOWN, SOWN + timedelta(days=3), week(4.0))
    assert [round(r["depletion"], 1) for r in later] == [2.0, 4.0, 6.0, 8.0]


def test_profile_from_catalog_item():
    fact = lambda v: {"value": v, "unit": "1", "evidence": "government"}  # noqa: E731
    item = {
        "requirements": {
            "water": {
                "kc_initial": fact(0.6),
                "kc_mid": fact(1.15),
                "kc_late": fact(0.8),
                "root_depth": fact({"min": 0.7, "max": 1.5}),
                "depletion_fraction": fact(0.4),
            }
        },
        "params": {
            f"stage_days_{s}": [fact(d) for d in ds]
            for s, ds in zip(
                ("initial", "development", "mid", "late"),
                ((30, 35, 40), (40, 40, 40), (40, 45, 50), (25, 30, 35)),
                strict=True,
            )
        },
    }
    w = profile_from_item(item, None)
    assert w.stage_days == (35, 40, 45, 30) and w.root_m == 1.1 and w.depletion_fraction == 0.4
    del item["params"]
    assert profile_from_item(item, None) is None  # no stages and no cycle: cannot say
    assert round(profile_from_item(item, (80, 120)).total_days) == 100  # standard split of the cycle
    del item["requirements"]["water"]["kc_mid"]
    assert profile_from_item(item, (80, 120)) is None
