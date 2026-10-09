from tests.test_household import owner  # noqa: F401  (fixture)

BASE = {"crop": "testcrop", "method": "direct", "start_date": "2026-10-20", "quantity": 12}


def test_planting_lifecycle(owner):  # noqa: F811
    made = owner.post("/api/v1/plantings", json=BASE | {"location": "Bed 1"})
    assert made.status_code == 201
    pid = made.json()["id"]
    assert [p["id"] for p in owner.get("/api/v1/plantings").json()] == [pid]

    step = lambda s: owner.patch(f"/api/v1/plantings/{pid}", json={"status": s})  # noqa: E731
    assert step("harvesting").status_code == 409  # cannot skip ahead
    assert step("sown").json()["status"] == "sown"
    assert step("germinated").status_code == 200
    assert step("transplanted").status_code == 409  # direct-sown plantings are not set out
    assert step("failed").status_code == 200
    assert step("sown").status_code == 409  # over for good
    assert owner.patch(f"/api/v1/plantings/{pid}", json={"notes": "slugs"}).json()["notes"] == "slugs"

    assert owner.delete(f"/api/v1/plantings/{pid}").status_code == 204
    assert owner.patch(f"/api/v1/plantings/{pid}", json={"notes": "x"}).status_code == 404


def test_planting_validation(owner):  # noqa: F811
    post = lambda **kw: owner.post("/api/v1/plantings", json=BASE | kw).status_code  # noqa: E731
    assert post(crop="nope") == 422
    assert post(set_out_date="2026-11-01") == 422  # direct sowing has no set-out
    assert post(method="transplant") == 422  # transplant needs a set-out date
    assert post(method="transplant", set_out_date="2026-10-01") == 422  # before sowing
    assert post(method="transplant", set_out_date="2026-11-30") == 201
    assert post(quantity=0) == 422
