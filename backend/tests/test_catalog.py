import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app import catalog as cat
from app.main import app
from app.routers import auth

FIXTURES = Path(__file__).parent / "fixtures"
REPO = Path(__file__).resolve().parents[2]


def test_the_real_catalog_loads_and_its_schema_files_are_current():
    loaded = cat.load(REPO / "catalog")
    assert "fao-ecocrop" in loaded.sources and loaded.sources["pfaf"].use == "link-only"
    check = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "catalog_schema.py"), "--check"], capture_output=True
    )
    assert check.returncode == 0, check.stdout.decode()


def test_variety_inherits_from_its_crop_and_overrides_win():
    c = cat.load(FIXTURES / "catalog")
    hardy = cat.effective(c, "variety", "testcrop-hardy")
    assert hardy["requirements"]["temperature"]["lethal_min"]["value"] == -3  # its own value
    assert hardy["requirements"]["temperature"]["base"]["value"] == 10  # inherited from the crop
    mine = cat.effective(
        c,
        "variety",
        "testcrop-hardy",
        {"requirements.temperature.lethal_min": {"value": -5, "evidence": "grower-reported", "estimate": True}},
    )
    assert mine["requirements"]["temperature"]["lethal_min"]["value"] == -5
    assert len(cat.effective(c, "crop", "testcrop")["params"]["days_to_maturity"]) == 2  # qualified statements kept


def test_private_pack_adds_and_overrides_but_never_breaks_startup():
    c = cat.load(FIXTURES / "catalog", FIXTURES / "catalog-private")
    crop = c.get("crop", "testcrop")
    assert crop["params"]["sowing_months"]["value"] == "Feb-Apr"  # added privately, even citing a link-only source
    assert crop["requirements"]["temperature"]["lethal_min"]["value"] == 0  # bundled fields kept
    assert c.origin[("crop", "testcrop")] == "bundled+private"
    assert c.origin[("crop", "mine")] == "private"
    assert c.get("crop", "broken") is None
    assert any("broken.yaml" in e for e in c.private_errors)


def write_catalog(tmp_path: Path, crop_patch: dict | None = None, sources: list | None = None) -> Path:
    root = tmp_path / "catalog"
    shutil.copytree(FIXTURES / "catalog", root)
    if sources is not None:
        (root / "sources.yaml").write_text(yaml.safe_dump(sources))
    if crop_patch is not None:
        path = root / "crops" / "testcrop.yaml"
        path.write_text(yaml.safe_dump(cat.deep_merge(yaml.safe_load(path.read_text()), crop_patch)))
    return root


LETHAL = ("requirements", "temperature", "lethal_min")


def lethal(value: dict) -> dict:
    return {"requirements": {"temperature": {"lethal_min": value}}}


@pytest.mark.parametrize(
    ("patch", "message"),
    [
        (lethal({"value": 0, "evidence": "traditional", "sources": []}), "needs a source, or estimate"),
        (lethal({"value": 0, "evidence": "traditional", "sources": [{"ref": "nowhere"}]}), "unknown source"),
        (lethal({"value": 0, "evidence": "traditional", "sources": [{"ref": "test-link"}]}), "only be linked"),
        (lethal({"value": 0, "evidence": "rumour", "estimate": True}), "evidence"),
        (
            {
                "requirements": {
                    "soil_temperature": {
                        "germination": {"value": {"min": 30, "max": 10}, "evidence": "model", "estimate": True}
                    }
                }
            },
            "min <= opt <= max",
        ),
        (
            {"requirements": {"temperature": {"lethal_minimum": {"value": 0, "evidence": "model", "estimate": True}}}},
            "Extra inputs",
        ),
        ({"slug": "Not A Slug"}, "slug"),
    ],
)
def test_bundled_catalog_problems_stop_loading(tmp_path, patch, message):
    with pytest.raises(cat.CatalogError, match=message):
        cat.load(write_catalog(tmp_path, patch))


def test_licence_gate_for_sources(tmp_path):
    nc_bundle = [
        {"id": "x", "title": "x", "url": "u", "license": "CC-BY-NC-4.0", "use": "bundle", "tos_reviewed": "2026-10-09"}
    ]
    with pytest.raises(cat.CatalogError, match="can't be bundled"):
        cat.load(write_catalog(tmp_path, sources=nc_bundle))


def test_variety_needs_an_existing_parent(tmp_path):
    root = write_catalog(tmp_path)
    (root / "varieties" / "orphan.yaml").write_text(
        "kind: variety\nslug: orphan\nparent: nothing\nnames: {en: [Orphan]}\n"
    )
    with pytest.raises(cat.CatalogError, match="parent crop 'nothing' not found"):
        cat.load(root)


# ---------------------------------------------------------------- API


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(auth, "registration_open", lambda db: True)
    auth.FAILS.clear()
    with TestClient(app) as c:
        yield c


def signup(client: TestClient, name: str) -> None:
    assert client.post("/api/v1/auth/register", json={"username": name, "password": "catalog pass"}).status_code == 200


def test_browse_catalog(client):
    signup(client, "cat1")
    status = client.get("/api/v1/catalog").json()
    assert status["counts"]["crop"] == 1 and status["counts"]["variety"] == 1
    assert client.get("/api/v1/catalog/crop").json()[0]["slug"] == "testcrop"
    item = client.get("/api/v1/catalog/variety/testcrop-hardy").json()
    assert item["data"]["requirements"]["temperature"]["base"]["value"] == 10
    assert "test-open" in item["sources"]
    assert client.get("/api/v1/catalog/crop/nothing").status_code == 404
    assert client.get("/api/v1/catalog/potions").status_code == 404


def test_household_override_and_reset(client):
    signup(client, "cat2")
    path = "requirements.temperature.lethal_min"
    mine = {"value": -2, "unit": "Cel", "evidence": "grower-reported", "estimate": True}
    assert client.put("/api/v1/catalog/crop/testcrop/overrides", json={"path": path, "value": mine}).status_code == 200
    item = client.get("/api/v1/catalog/crop/testcrop").json()
    assert item["data"]["requirements"]["temperature"]["lethal_min"]["value"] == -2
    assert item["overrides"] == {path: mine}

    for bad in (
        {"path": path, "value": {"value": -2, "evidence": "grower-reported"}},  # uncited, not an estimate
        {"path": "requirements.temperature.lethal_minimum", "value": mine},  # unknown field
        {"path": "slug", "value": "other"},
        {"path": "Requirements..x", "value": 1},
    ):
        assert client.put("/api/v1/catalog/crop/testcrop/overrides", json=bad).status_code == 422

    assert client.delete("/api/v1/catalog/crop/testcrop/overrides", params={"path": path}).status_code == 200
    assert (
        client.get("/api/v1/catalog/crop/testcrop").json()["data"]["requirements"]["temperature"]["lethal_min"]["value"]
        == 0
    )


def test_overrides_belong_to_one_household_and_need_edit_rights(client, monkeypatch):
    signup(client, "cat3")
    path = "requirements.temperature.base"
    value = {"value": 8, "evidence": "grower-reported", "estimate": True}
    client.put("/api/v1/catalog/crop/testcrop/overrides", json={"path": path, "value": value})
    token = client.post("/api/v1/household/invites", json={"role": "viewer"}).json()["token"]

    viewer = TestClient(app)
    monkeypatch.setattr(auth, "registration_open", lambda db: False)
    viewer.post("/api/v1/auth/register", json={"username": "cat3viewer", "password": "viewer pass", "invite": token})
    assert (
        viewer.get("/api/v1/catalog/crop/testcrop").json()["data"]["requirements"]["temperature"]["base"]["value"] == 8
    )
    assert viewer.put("/api/v1/catalog/crop/testcrop/overrides", json={"path": path, "value": value}).status_code == 403

    monkeypatch.setattr(auth, "registration_open", lambda db: True)
    other = TestClient(app)
    signup(other, "cat3other")
    assert (
        other.get("/api/v1/catalog/crop/testcrop").json()["data"]["requirements"]["temperature"]["base"]["value"] == 10
    )
