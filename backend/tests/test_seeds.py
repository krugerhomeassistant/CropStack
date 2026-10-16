from pathlib import Path

from app import catalog as cat
from app import external
from tests.e2e_server import fake_archive
from tests.test_auth_garden import GARDEN
from tests.test_household import owner  # noqa: F401  (fixture)


def test_seeds_are_kept_per_household_and_must_be_catalog_crops(owner):  # noqa: F811
    assert owner.get("/api/v1/seeds").json() == []
    assert owner.put("/api/v1/seeds", json={"crops": ["testcrop", "nonsense"]}).status_code == 422
    assert owner.put("/api/v1/seeds", json={"crops": ["testcrop"]}).json() == ["testcrop"]
    assert owner.put("/api/v1/seeds", json={"crops": []}).json() == []  # replaces the whole list


def test_the_plan_leans_on_seeds_you_have_and_lists_the_rest_to_buy(owner, monkeypatch):  # noqa: F811
    from app.main import app

    monkeypatch.setattr(app.state, "catalog", cat.load(Path(__file__).resolve().parents[2] / "catalog"))
    monkeypatch.setattr(external, "fetch_climate_archive", fake_archive)
    owner.put("/api/v1/sites/current", json=GARDEN)
    for n in range(1, 4):
        owner.post("/api/v1/beds", json={"name": f"Bed {n}", "width": 1.2, "length": 2.4})
    base = owner.get("/api/v1/plan/year").json()
    crops = {i["crop"] for i in base["items"]}
    assert crops and {b["crop"] for b in base["buy"]} == crops and base["seeds"] == []  # nothing owned: buy it all
    others = [c["slug"] for c in owner.get("/api/v1/catalog/crop").json() if c["slug"] not in crops][:12]
    owner.put("/api/v1/seeds", json={"crops": others})
    plan = owner.get("/api/v1/plan/year").json()
    used = {i["crop"] for i in plan["items"]}
    print(len(others), sorted(used & set(others)))
    assert used & set(others), "seed you have should pull crops into the plan"
    assert all(i["have_seed"] == (i["crop"] in others) for i in plan["items"])
    assert not {b["crop"] for b in plan["buy"]} & set(others)
