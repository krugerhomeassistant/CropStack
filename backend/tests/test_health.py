from fastapi.testclient import TestClient

from app import VERSION
from app.main import app


def test_health_reports_version_and_db() -> None:
    with TestClient(app) as client:
        resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok" and resp.json()["version"] == VERSION
    assert "jobs" in resp.json()
    assert resp.headers["Cache-Control"] == "no-store"
    assert resp.headers["X-Frame-Options"] == "DENY"


def test_pages_are_rechecked_but_hashed_assets_are_cached(tmp_path, monkeypatch) -> None:
    from app.config import get_settings
    from app.main import create_app

    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html></html>")
    (tmp_path / "sw.js").write_text("//")
    (tmp_path / "assets" / "index-abc.js").write_text("//")
    monkeypatch.setenv("CROPSTACK_STATIC_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        with TestClient(create_app()) as client:
            cache = {
                p: client.get(p).headers["Cache-Control"] for p in ("/", "/sw.js", "/garden", "/assets/index-abc.js")
            }
    finally:
        get_settings.cache_clear()
    assert cache["/assets/index-abc.js"].endswith("immutable")
    assert cache["/"] == cache["/sw.js"] == cache["/garden"] == "no-cache"
