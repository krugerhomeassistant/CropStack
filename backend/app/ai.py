"""The garden assistant's provider calls: Ollama (local), any OpenAI-compatible API, or Anthropic.

`build_request` and `parse_reply` are pure so each provider's wire format is tested without a network.
"""

import httpx

from .external import USER_AGENT, ExternalError

PROVIDERS = ("ollama", "openai", "anthropic")
DEFAULT_URL = {
    "ollama": "http://host.docker.internal:11434",
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
}
MAX_TOKENS = 1024


def build_request(cfg: dict, system: str, messages: list[dict]) -> tuple[str, dict, dict]:
    """The URL, headers and JSON body for one chat turn. `messages` are {role: user|assistant, content}."""
    provider = cfg["provider"]
    base = (cfg.get("base_url") or DEFAULT_URL[provider]).rstrip("/")
    headers = {"User-Agent": USER_AGENT}
    key = cfg.get("api_key", "")
    if provider == "anthropic":
        headers |= {"x-api-key": key, "anthropic-version": "2023-06-01"}
        body = {"model": cfg["model"], "max_tokens": MAX_TOKENS, "system": system, "messages": messages}
        return f"{base}/v1/messages", headers, body
    if key:
        headers["Authorization"] = f"Bearer {key}"
    chat = [{"role": "system", "content": system}, *messages]
    if provider == "ollama":
        return f"{base}/api/chat", headers, {"model": cfg["model"], "messages": chat, "stream": False}
    return f"{base}/chat/completions", headers, {"model": cfg["model"], "messages": chat, "max_tokens": MAX_TOKENS}


def parse_reply(provider: str, data: dict) -> str:
    try:
        if provider == "anthropic":
            return "".join(b["text"] for b in data["content"] if b.get("type") == "text").strip()
        if provider == "ollama":
            return data["message"]["content"].strip()
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as e:
        raise ExternalError("The AI service sent a reply CropStack could not read") from e


def ask(cfg: dict, system: str, messages: list[dict], timeout: float = 120) -> str:
    url, headers, body = build_request(cfg, system, messages)
    try:
        resp = httpx.post(url, headers=headers, json=body, timeout=timeout)
    except httpx.HTTPError as e:
        raise ExternalError(f"Could not reach {httpx.URL(url).host}: {e.__class__.__name__}") from e
    if resp.status_code != 200:
        raise ExternalError(f"{httpx.URL(url).host} answered {resp.status_code}; check the address, model and key")
    try:
        data = resp.json()
    except ValueError as e:
        raise ExternalError("The AI service sent a reply CropStack could not read") from e
    return parse_reply(cfg["provider"], data)
