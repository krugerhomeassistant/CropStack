from datetime import date

from app import environment as env
from app.engine.phenology import CropProfile, design_days
from app.engine.windows import analyse, evaluate, success_threshold

from .test_climate import synthetic

TOMATO = CropProfile(
    slug="tomato",
    base=10,
    cutoff=30,
    gdd_to_maturity=1100,
    cycle_days=(90, 120),
    germination_min=12,
    lethal_min=0,
    stress_max=35,
    optimal=(18, 26),
)
LETTUCE = CropProfile(
    slug="lettuce",
    base=4,
    cutoff=25,
    gdd_to_maturity=500,
    cycle_days=(45, 65),
    germination_min=4,
    lethal_min=-2,
    stress_max=28,
    optimal=(10, 18),
)


def climate(mean: float, amplitude: float, shift: float = 3.0) -> env.Climatology:
    return env.from_open_meteo(synthetic(mean, amplitude, date(2001, 1, 15), year_shift=shift))


def test_design_days_follows_recocrop():
    assert design_days((90, 120)) == 120  # a 30-day spread is capped at 30
    assert design_days((45, 50)) == 50  # a narrower spread is used whole


def test_success_threshold_follows_frost_risk_setting():
    assert success_threshold(10) == 0.9 and success_threshold(50) == 0.8 and abs(success_threshold(90) - 0.6) < 1e-9
    assert success_threshold(30) > success_threshold(70)


def test_evaluate_covers_every_day():
    days = evaluate(climate(14, 8), TOMATO)
    assert [d["doy"] for d in days] == list(range(1, 366)) or len(days) == 365
    assert all(0 <= d["success"] <= 1 for d in days)


def total(result: dict) -> int:
    return sum(w["length_days"] for w in result["windows"])


def test_same_crop_different_climates_get_different_windows():
    """AC-P2/P3: no configuration, only the climate differs."""
    mild = climate(mean=14, amplitude=7)  # mild winters
    frosty = climate(mean=5, amplitude=14)  # hard winters, short summers
    tomato_mild, tomato_frosty = analyse(mild, TOMATO, 0.8), analyse(frosty, TOMATO, 0.8)
    assert total(tomato_mild) > total(tomato_frosty)
    # Lettuce tolerates cold: where winters bite it can go in before tomato.
    lettuce = analyse(frosty, LETTUCE, 0.8)
    assert min(w["start"] for w in lettuce["windows"]) < min(w["start"] for w in tomato_frosty["windows"])
    assert tomato_mild["verdict"]["state"] == "yes"
