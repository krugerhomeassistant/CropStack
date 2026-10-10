"""The AI co-pilot (SPEC §12.4): the owner picks a provider; members ask questions grounded in the garden.

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
    "You are the garden co-pilot of CropStack, a home garden and homestead planner. Answer briefly and practically "
    "for this household's garden. Use the garden facts below; say so when you are unsure or when a local "
    "extension service should be asked. Never claim to have changed anything: you can only advise.\n\n"
)


class AiIn(BaseModel):
    provider: Literal["ollama", "openai", "anthropic"]
    base_url: str = Field(default="", max_length=200, pattern=r"^(https?://\S+)?$")
    model: str = Field(min_length=1, max_length=100)
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


def _public(household: Household) -> dict:
    cfg = household.ai
    return {
        "configured": bool(cfg.get("provider")),
        "provider": cfg.get("provider", ""),
        "base_url": cfg.get("base_url", ""),
        "model": cfg.get("model", ""),
        "has_key": bool(cfg.get("api_key")),
        "default_urls": ai.DEFAULT_URL,
    }


def _configured(household: Household) -> dict:
    if not household.ai.get("provider"):
        raise HTTPException(409, "The AI co-pilot is not set up yet. An owner can do it in Settings.")
    return household.ai


def context(db, household_id: int) -> str:
    """What the co-pilot may know: the site, the plantings and the open jobs. No names, no account data."""
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
    key = household.ai.get("api_key", "") if body.api_key is None else body.api_key
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
def test_ai(me: OwnerDep, db: SessionDep) -> dict:
    cfg = _configured(_household(db, me))
    try:
        reply = ai.ask(cfg, "Reply with the single word OK.", [{"role": "user", "content": "ping"}], timeout=60)
    except external.ExternalError as e:
        raise HTTPException(502, str(e)) from e
    return {"reply": reply[:200]}


@router.post("/ask")
def ask(body: AskIn, me: EditorDep, db: SessionDep) -> dict:
    cfg = _configured(_household(db, me))
    try:
        reply = ai.ask(cfg, SYSTEM + context(db, me.household_id), [t.model_dump() for t in body.messages])
    except external.ExternalError as e:
        raise HTTPException(502, str(e)) from e
    return {"reply": reply}
