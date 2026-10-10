"""The garden assistant (SPEC §12.4): the owner picks a provider; members ask questions grounded in the garden.

The key lives in the household row on the server and is never sent back to the browser.
"""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import select

from .. import ai, external
from ..deps import EditorDep, MemberDep, OwnerDep, SessionDep
from ..models import Household, Planting, Site, Task

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

SYSTEM = (
    "You are the garden assistant of CropStack, a home garden and homestead planner. Answer briefly and practically "
    "for this household's garden. Use the garden facts below; say so when you are unsure or when a local "
    "extension service should be asked. Never claim to have changed anything: you can only advise.\n\n"
)


class AiIn(BaseModel):
    provider: Literal["anthropic", "openai", "openrouter", "ollama", "custom"]
    base_url: str = Field(default="", max_length=200, pattern=r"^(https?://\S+)?$")  # blank = the provider's own
    model: str = Field(default="", max_length=100)  # blank = the provider's default
    api_key: str | None = Field(default=None, max_length=300)  # None keeps the saved key, "" removes it


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class AskIn(BaseModel):
    messages: list[Turn] = Field(min_length=1, max_length=20)


def _household(db, member) -> Household:
    household = db.get(Household, member.household_id)
    assert household
    return household


def _effective(household: Household, override: dict | None = None) -> dict:
    return ai.config(household.ai, override or {})


def _public(household: Household) -> dict:
    cfg = _effective(household)
    return {
        "configured": ai.enabled(cfg),
        "provider": cfg["provider"],
        "base_url": household.ai.get("base_url", ""),
        "model": household.ai.get("model", ""),
        "has_key": bool(cfg["api_key"]),
        "key_hint": cfg["api_key"][-4:] if len(cfg["api_key"]) > 8 else "",
        "providers": {p: {"base_url": u, "model": m} for p, (u, m) in ai.PROVIDERS.items()},
    }


def _configured(household: Household) -> dict:
    cfg = _effective(household)
    if not ai.enabled(cfg):
        raise HTTPException(409, "The garden assistant is not set up yet. An owner can do it in Settings.")
    return cfg


def context(db, household_id: int) -> str:
    """What the assistant may know: the site, the plantings and the open jobs. No names, no account data."""
    site = db.exec(select(Site).where(Site.household_id == household_id)).first()
    lines = (
        [f"Garden: {site.name} at {site.latitude:.2f}, {site.longitude:.2f}; soil: {site.soil or 'unknown'}"]
        if site
        else []
    )
    plantings = db.exec(select(Planting).where(Planting.household_id == household_id).limit(60)).all()
    lines += [
        f"Planting: {p.crop} x{p.quantity}, {p.status}, from {p.start_date}, {p.location or 'no place'}"
        for p in plantings
    ]
    tasks = db.exec(select(Task).where(Task.household_id == household_id, Task.status == "open").limit(30)).all()
    lines += [f"Open job: {t.title} (ideal {t.ideal})" for t in tasks]
    return "\n".join(lines)


@router.get("")
def get_ai(me: MemberDep, db: SessionDep) -> dict:
    return _public(_household(db, me))


@router.put("")
def save_ai(body: AiIn, me: OwnerDep, db: SessionDep) -> dict:
    household = _household(db, me)
    saved = household.ai
    key = body.api_key
    if key is None:  # keep the saved key, but never carry it over to a different provider
        key = saved.get("api_key", "") if saved.get("provider") == body.provider else ""
    # shortcut: the key is stored as plain text in the SQLite file, next to secret.key; encrypt it at rest if the
    # data folder ever leaves the owner's machine (backups to a cloud, shared hosts).
    household.ai = body.model_dump(exclude={"api_key"}) | {"api_key": key}
    db.add(household)
    db.commit()
    return _public(household)


@router.delete("")
def clear_ai(me: OwnerDep, db: SessionDep) -> dict:
    household = _household(db, me)
    household.ai = {}
    db.add(household)
    db.commit()
    return _public(household)


@router.post("/test")
def test_ai(body: AiIn, me: OwnerDep, db: SessionDep) -> dict:
    """Tries the settings in the form without saving them; a failure is an answer, not an error."""
    household = _household(db, me)
    override = body.model_dump()
    if body.api_key is None and household.ai.get("provider") == body.provider:
        override["api_key"] = household.ai.get("api_key", "")
    try:
        reply = ai.ask(
            _effective(household, override), "Reply with the single word OK.", [{"role": "user", "content": "ping"}]
        )
    except external.ExternalError as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "reply": reply[:200]}


@router.post("/ask")
def ask(body: AskIn, me: EditorDep, db: SessionDep) -> dict:
    cfg = _configured(_household(db, me))
    try:
        reply = ai.ask(cfg, SYSTEM + context(db, me.household_id), [t.model_dump() for t in body.messages])
    except external.ExternalError as e:
        raise HTTPException(502, str(e)) from e
    return {"reply": reply}
