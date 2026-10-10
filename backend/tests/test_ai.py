import pytest

from app import ai, external
from app.routers import ai as ai_router
from tests.test_household import owner  # noqa: F401  (fixture)

MSG = [{"role": "user", "content": "hi"}]


@pytest.mark.parametrize(
    ("provider", "path", "auth"),
    [
        ("ollama", "/api/chat", "Authorization"),
        ("openai", "/chat/completions", "Authorization"),
        ("anthropic", "/v1/messages", "x-api-key"),
    ],
)
def test_each_provider_gets_its_own_wire_format(provider, path, auth):
    cfg = {"provider": provider, "model": "m", "api_key": "k", "base_url": "http://x.test/"}
    url, headers, body = ai.build_request(cfg, "sys", MSG)
    assert url == f"http://x.test{path}" and auth in headers and body["model"] == "m"
    assert ("system" in body) == (provider == "anthropic")  # the others carry it as the first message


def test_replies_are_parsed_and_junk_is_refused():
    assert ai.parse_reply("openai", {"choices": [{"message": {"content": " hi "}}]}) == "hi"
    assert ai.parse_reply("ollama", {"message": {"content": "hi"}}) == "hi"
    assert ai.parse_reply("anthropic", {"content": [{"type": "text", "text": "hi"}]}) == "hi"
    with pytest.raises(external.ExternalError):
        ai.parse_reply("openai", {"error": "no"})


def test_key_is_saved_kept_and_never_returned(owner, monkeypatch):  # noqa: F811
    assert owner.get("/api/v1/ai").json()["configured"] is False
    assert owner.post("/api/v1/ai/ask", json={"messages": [{"role": "user", "content": "q"}]}).status_code == 409
    body = {"provider": "openai", "model": "gpt-x", "base_url": "", "api_key": "sk-secret"}
    saved = owner.put("/api/v1/ai", json=body).json()
    assert saved["has_key"] and "sk-secret" not in str(saved)
    owner.put("/api/v1/ai", json=body | {"api_key": None, "model": "gpt-y"})  # None keeps the key
    seen = {}
    monkeypatch.setattr(
        ai_router.ai, "ask", lambda cfg, system, messages, timeout=0: seen.update(cfg=cfg, system=system) or "hello"
    )
    assert owner.post("/api/v1/ai/ask", json={"messages": [{"role": "user", "content": "q"}]}).json() == {
        "reply": "hello"
    }
    assert seen["cfg"]["api_key"] == "sk-secret" and seen["cfg"]["model"] == "gpt-y"
    assert any(s["id"] == "ai" for s in owner.get("/api/v1/household/data-sources").json())
    assert owner.put("/api/v1/ai", json=body | {"api_key": ""}).json()["has_key"] is False
    assert owner.delete("/api/v1/ai").json()["configured"] is False
