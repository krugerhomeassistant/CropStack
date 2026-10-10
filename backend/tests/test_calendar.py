from tests.test_household import owner  # noqa: F401  (fixture)


def test_calendar_lists_sowing_and_harvest_jobs_by_day_and_limits_the_range(owner):  # noqa: F811
    made = owner.post(
        "/api/v1/plantings", json={"crop": "testcrop", "method": "direct", "start_date": "2026-10-12", "quantity": 4}
    )
    assert made.status_code == 201
    events = owner.get("/api/v1/calendar", params={"start": "2026-10-01", "end": "2027-01-05"}).json()
    assert isinstance(events, list), events
    kinds = {e["kind"] for e in events}
    assert "sow" in kinds and "harvest" in kinds and all(k in ("sow", "set_out", "harvest") for k in kinds)
    assert events == sorted(events, key=lambda e: e["date"])
    assert next(e for e in events if e["kind"] == "sow")["date"] == "2026-10-12"
    assert owner.get("/api/v1/calendar", params={"start": "2026-10-01", "end": "2028-01-01"}).status_code == 422
