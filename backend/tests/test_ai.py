import pytest

from app import ai, external
from app.routers import ai as ai_router
from tests.test_household import owner  # noqa: F401  (fixture)

MSG = [{"role": "user", "content": "hi"}]


@pytest.mark.parametrize(
    ("provider", "path", "auth", "cap"),
    [
        ("ollama", "/chat/completions", "Authorization", "max_tokens"),
        ("openai", "/chat/completions", "Authorization", "max_completion_tokens"),
        ("openrouter", "/chat/completions", "Authorization", "max_tokens"),
        ("custom", "/chat/completions", "Authorization", "max_tokens"),
        ("anthropic", "/v1/messages", "x-api-key", "max_tokens"),
    ],
)
def test_each_provider_gets_its_own_wire_format(provider, path, auth, cap):
    cfg = ai.config({"provider": provider, "model": "m", "api_key": "k", "base_url": "http://x.test/"})
    url, headers, body = ai.build_request(cfg, "sys", MSG)
    assert url == f"http://x.test{path}" and auth in headers and body["model"] == "m" and cap in body
    assert ("system" in body) == (provider == "anthropic")  # the others carry it as the first message


def test_blank_url_and_model_use_the_provider_defaults_and_switching_drops_the_old_key():
    cfg = ai.config({"provider": "openai", "api_key": "sk-1"}, {"provider": "anthropic"})
    assert cfg["api_key"] == "" and cfg["model"] == ai.PROVIDERS["anthropic"][1]
    assert ai.config({"provider": "openai"})["base_url"] == ai.PROVIDERS["openai"][0]
    with pytest.raises(external.ExternalError):  # a custom service has no default address
        ai.build_request(ai.config({"provider": "custom"}), "s", MSG)


def test_replies_are_parsed_thinking_is_dropped_and_junk_is_refused():
    assert ai.parse_reply("openai", {"choices": [{"message": {"content": " hi "}}]}) == "hi"
    assert ai.parse_reply("ollama", {"choices": [{"message": {"content": "<think>hm</think>hi"}}]}) == "hi"
    assert ai.parse_reply("anthropic", {"content": [{"type": "text", "text": "hi"}]}) == "hi"
    with pytest.raises(external.ExternalError):
        ai.parse_reply("openai", {"error": "no"})


def test_key_is_saved_kept_dropped_on_provider_change_and_never_returned(owner, monkeypatch):  # noqa: F811
    assert owner.get("/api/v1/ai").json()["configured"] is False
    assert owner.post("/api/v1/ai/ask", json={"messages": [{"role": "user", "content": "q"}]}).status_code == 409
    body = {"provider": "openai", "model": "", "base_url": "", "api_key": "sk-secret-1234"}
    saved = owner.put("/api/v1/ai", json=body).json()
    assert saved["has_key"] and saved["key_hint"] == "1234" and "sk-secret" not in str(saved)
    owner.put("/api/v1/ai", json=body | {"api_key": None, "model": "gpt-y"})  # None keeps the key
    seen = {}
    monkeypatch.setattr(ai_router.ai, "ask", lambda cfg, system, messages: seen.update(cfg=cfg) or "hello")
    assert owner.post("/api/v1/ai/ask", json={"messages": [{"role": "user", "content": "q"}]}).json() == {
        "reply": "hello"
    }
    assert seen["cfg"]["api_key"] == "sk-secret-1234" and seen["cfg"]["model"] == "gpt-y"
    tested = owner.post("/api/v1/ai/test", json=body | {"api_key": None}).json()  # unsaved form values, saved key
    assert tested == {"ok": True, "reply": "hello"} and seen["cfg"]["api_key"] == "sk-secret-1234"
    assert any(s["id"] == "ai" for s in owner.get("/api/v1/household/data-sources").json())
    assert owner.put("/api/v1/ai", json=body | {"provider": "anthropic", "api_key": None}).json()["has_key"] is False
    assert owner.delete("/api/v1/ai").json()["configured"] is False
