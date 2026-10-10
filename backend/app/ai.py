"""The garden assistant's provider calls (httpx, no SDKs), after Bloomery's `ai.py`.

Providers: anthropic (/v1/messages); openai, openrouter, ollama and custom speak the OpenAI /chat/completions schema.
Config precedence: CROPSTACK_AI_* environment < the household's saved settings < a one-off override (Test button).
`config`, `build_request` and `parse_reply` are pure so each provider's format is tested without a network.
"""

import re

import httpx

from .config import get_settings
from .external import USER_AGENT, ExternalError

# provider -> (default base URL, default model)
PROVIDERS: dict[str, tuple[str, str]] = {
    "anthropic": ("https://api.anthropic.com", "claude-haiku-4-5-20251001"),
    "openai": ("https://api.openai.com/v1", "gpt-5-mini"),
    "openrouter": ("https://openrouter.ai/api/v1", "openrouter/auto"),
    "ollama": ("http://host.docker.internal:11434/v1", "llama3.2:3b"),
    "custom": ("", ""),
}
KEYS = ("provider", "base_url", "model", "api_key")
MAX_TOKENS = 1024
_THINK = re.compile(r"<think>.*?</think>", re.S)  # reasoning models (qwen3, deepseek) print their thinking first


def config(*layers: dict) -> dict:
    """The effective settings: env < each layer in order. Switching provider drops the earlier url, model and key."""
    s = get_settings()
    cfg = {"provider": s.ai_provider, "base_url": s.ai_base_url, "model": s.ai_model, "api_key": s.ai_api_key}
    for layer in layers:
        if layer.get("provider") and layer["provider"] != cfg["provider"]:
            cfg |= {"provider": layer["provider"], "base_url": "", "model": "", "api_key": ""}
        cfg |= {k: v for k, v in layer.items() if k in KEYS and k != "provider" and v is not None}
    base, model = PROVIDERS.get(cfg["provider"], ("", ""))
    cfg["base_url"] = (cfg["base_url"] or base).rstrip("/")
    cfg["model"] = cfg["model"] or model
    return cfg


def enabled(cfg: dict) -> bool:
    return cfg["provider"] in PROVIDERS


def build_request(cfg: dict, system: str, messages: list[dict]) -> tuple[str, dict, dict]:
    """The URL, headers and JSON body for one chat turn. `messages` are {role: user|assistant, content}."""
    provider, base, model, key = cfg["provider"], cfg["base_url"], cfg["model"], cfg["api_key"]
    if provider not in PROVIDERS:
        raise ExternalError("The garden assistant is turned off")
    if not base or not model:
        raise ExternalError("This service needs an address and a model")
    headers = {"User-Agent": USER_AGENT}
    if provider == "anthropic":
        headers |= {"x-api-key": key, "anthropic-version": "2023-06-01"}
        return (
            f"{base}/v1/messages",
            headers,
            {"model": model, "max_tokens": MAX_TOKENS, "system": system, "messages": messages},
        )
    if key:
        headers["Authorization"] = f"Bearer {key}"
    body = {"model": model, "messages": [{"role": "system", "content": system}, *messages]}
    # The GPT-5 family rejects max_tokens and counts reasoning tokens inside the cap.
    body |= {"max_completion_tokens": MAX_TOKENS * 4} if provider == "openai" else {"max_tokens": MAX_TOKENS}
    return f"{base}/chat/completions", headers, body


def parse_reply(provider: str, data: dict) -> str:
    try:
        if provider == "anthropic":
            text = "".join(b["text"] for b in data["content"] if b.get("type") == "text")
        else:
            text = data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError, AttributeError) as e:
        raise ExternalError("The AI service sent a reply CropStack could not read") from e
    return _THINK.sub("", text).strip()


def _status_error(resp: httpx.Response) -> ExternalError:
    try:  # Anthropic and OpenAI both answer {"error": {"message": ...}}
        detail = resp.json()["error"]["message"]
    except Exception:
        detail = resp.text[:300]
    return ExternalError(f"The AI service answered {resp.status_code}: {detail}")


def ask(cfg: dict, system: str, messages: list[dict]) -> str:
    url, headers, body = build_request(cfg, system, messages)
    try:
        resp = httpx.post(url, headers=headers, json=body, timeout=get_settings().ai_timeout)
    except httpx.HTTPError as e:
        raise ExternalError(f"Could not reach the AI service at {cfg['base_url']}: {e.__class__.__name__}") from e
    if resp.status_code >= 400:
        raise _status_error(resp)
    try:
        data = resp.json()
    except ValueError as e:
        raise ExternalError("The AI service sent a reply CropStack could not read") from e
    return parse_reply(cfg["provider"], data)
