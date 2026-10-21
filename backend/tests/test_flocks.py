from datetime import UTC, datetime

from tests.test_household import owner  # noqa: F401  (fixture)


def test_a_flock_lives_in_a_coop_that_is_never_planted_and_logs_eggs(owner):  # noqa: F811
    today = datetime.now(UTC).date().isoformat()
    coop = owner.post("/api/v1/beds", json={"name": "Coop 1", "kind": "coop", "width": 2, "length": 3}).json()
    bed = owner.post("/api/v1/beds", json={"name": "Bed 1", "width": 1.2, "length": 2.4}).json()
    assert owner.post("/api/v1/flocks", json={"name": "x", "got_on": today, "coop_id": bed["id"]}).status_code == 422
    flock = owner.post(
        "/api/v1/flocks",
        json={"name": "Hens", "breed": "Rhode Island Red", "count": 4, "got_on": today, "coop_id": coop["id"]},
    ).json()
    assert flock["coop"] == "Coop 1" and flock["coop_m2"] == 6.0 and flock["wanted_m2"] == 5.6  # a hint, not a limit
    url = f"/api/v1/flocks/{flock['id']}/eggs"
    assert owner.post(url, json={"laid_on": today, "count": 3}).json()["eggs_today"] == 3
    again = owner.post(url, json={"laid_on": today, "count": 2}).json()  # the same day replaces, never doubles
    assert again["eggs_today"] == 2 and again["eggs_week"] == 2 and again["per_hen_day"] == 0.07
    assert owner.patch(f"/api/v1/flocks/{flock['id']}", json={"count": 6}).json()["count"] == 6
    assert owner.get("/api/v1/flocks").json()[0]["name"] == "Hens"
    kinds = {b["name"]: b["kind"] for b in owner.get("/api/v1/beds").json()}
    assert kinds == {"Coop 1": "coop", "Bed 1": "bed"}
    assert owner.delete(f"/api/v1/flocks/{flock['id']}").status_code == 204
    assert owner.get("/api/v1/flocks").json() == []
    assert owner.post(url, json={"laid_on": today, "count": 1}).status_code == 404
