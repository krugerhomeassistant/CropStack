"""Polite fetching with snapshots (SPEC §16.1, docs/research/catalog-data-sources.md → Pipeline).

- identifying User-Agent, robots.txt obeyed, at least MIN_INTERVAL seconds between requests to one host;
- every raw response is stored once under its SHA-256 in CACHE (outside git: raw copies may be copyrighted and
  are kept only to verify values) and recorded in snapshots.lock, which is committed;
- extraction always reads from the cache, so a run can be repeated offline from the lock.
"""

from __future__ import annotations

import hashlib
import time
import urllib.robotparser
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / ".ingest-cache"
LOCK = Path(__file__).with_name("snapshots.lock")
USER_AGENT = "CropStack-catalog-ingest/1.0 (+https://github.com/krugerhomeassistant/CropStack)"
MIN_INTERVAL = 2.0  # seconds between requests to the same host

_last_request: dict[str, float] = {}
_robots: dict[str, urllib.robotparser.RobotFileParser] = {}


class FetchError(Exception):
    pass


def read_lock() -> dict[str, dict]:
    return (yaml.safe_load(LOCK.read_text()) or {}) if LOCK.exists() else {}


def write_lock(lock: dict[str, dict]) -> None:
    header = "# Raw source snapshots used by the catalog (scripts/ingest). Files live in .ingest-cache/<sha256>.\n"
    LOCK.write_text(header + yaml.safe_dump(lock, sort_keys=True, allow_unicode=True))


def _allowed(client: httpx.Client, url: str) -> bool:
    parts = urlsplit(url)
    host = f"{parts.scheme}://{parts.netloc}"
    if host not in _robots:
        parser = urllib.robotparser.RobotFileParser()
        response = client.get(f"{host}/robots.txt")
        # RFC 9309: 4xx = no rules; 5xx or no answer = assume everything is disallowed.
        if response.status_code >= 500:
            parser.parse(["User-agent: *", "Disallow: /"])
        else:
            parser.parse(response.text.splitlines() if response.status_code == 200 else [])
        _robots[host] = parser
    return _robots[host].can_fetch(USER_AGENT, url)


def _throttle(url: str) -> None:
    host = urlsplit(url).netloc
    wait = _last_request.get(host, 0) + MIN_INTERVAL - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    _last_request[host] = time.monotonic()


def fetch(key: str, url: str, client: httpx.Client) -> str:
    """Download url, store it in the cache, record it in the lock under key; returns the sha256."""
    if not _allowed(client, url):
        raise FetchError(f"robots.txt disallows {url}")
    _throttle(url)
    response = client.get(url)
    if response.status_code != 200:
        raise FetchError(f"{url}: HTTP {response.status_code}")
    digest = hashlib.sha256(response.content).hexdigest()
    CACHE.mkdir(exist_ok=True)
    (CACHE / digest).write_bytes(response.content)
    lock = read_lock()
    previous = lock.get(key, {})
    retrieved = previous["retrieved"] if previous.get("sha256") == digest else date.today()
    lock[key] = {"url": url, "sha256": digest, "retrieved": retrieved}
    write_lock(lock)
    return digest


def client() -> httpx.Client:
    return httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True)


def snapshot(key: str) -> tuple[bytes, dict]:
    """The locked raw copy for key and its lock entry; fails if it was never fetched on this machine."""
    entry = read_lock().get(key)
    if not entry:
        raise FetchError(f"{key} is not in snapshots.lock; run `python scripts/ingest fetch` first")
    path = CACHE / entry["sha256"]
    if not path.exists():
        raise FetchError(f"{key}: snapshot {entry['sha256'][:12]}… missing from {CACHE}; run fetch again")
    return path.read_bytes(), entry
