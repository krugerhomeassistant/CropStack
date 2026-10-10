"""The household: its name, members and roles, and invite links for new members."""

import secrets
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, func, select

from .. import ai
from ..deps import MemberDep, OwnerDep, SessionDep
from ..models import Household, Invite, Membership, User, now
from .auth import token_hash, valid_invite

router = APIRouter(prefix="/api/v1", tags=["household"])

INVITE_DAYS = 7
Role = Literal["owner", "member", "viewer"]


class HouseholdIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class RoleIn(BaseModel):
    role: Role


class InviteIn(BaseModel):
    role: Role = "member"


class HouseholdSettings(BaseModel):
    """Household-wide switches. Turning a source off stops every call to it; features that need it say so."""

    forecast: bool = True
    place_search: bool = True


def household_settings(household: Household) -> HouseholdSettings:
    return HouseholdSettings(**household.settings)


# What leaves the server, shown on Settings → Data sources (SPEC §16, P7).
DATA_SOURCES = [
    {
        "id": "climate",
        "name": "Open-Meteo historical weather (ERA5, ERA5-Land)",
        "url": "https://open-meteo.com/en/docs/historical-weather-api",
        "sends": "Garden coordinates",
        "when": "Once per location, and once a year for the newest year",
        "used_for": "Climate, frost risk, planting windows",
        "licence": "CC BY 4.0",
        "switch": None,  # everything depends on it; there is no manual fallback yet
    },
    {
        "id": "forecast",
        "name": "Open-Meteo forecast",
        "url": "https://open-meteo.com/en/docs",
        "sends": "Garden coordinates",
        "when": "About every 3 hours",
        "used_for": "Today's weather, the next 16 days, this month against normal",
        "licence": "CC BY 4.0",
        "switch": "forecast",
    },
    {
        "id": "place_search",
        "name": "OpenStreetMap Nominatim",
        "url": "https://nominatim.org/",
        "sends": "What you type in place search",
        "when": "Only when you search",
        "used_for": "Finding your garden by town, address or postal code",
        "licence": "ODbL",
        "switch": "place_search",
    },
]


def _owners(db: Session, household_id: int) -> int:
    query = select(func.count()).select_from(Membership)
    return db.exec(query.where(Membership.household_id == household_id, Membership.role == "owner")).one()


def _member(db: Session, owner: Membership, user_id: int) -> Membership:
    membership = db.get(Membership, user_id)
    if not membership or membership.household_id != owner.household_id:
        raise HTTPException(404, "No such member")
    return membership


@router.get("/household")
def get_household(me: MemberDep, db: SessionDep) -> dict:
    household = db.get(Household, me.household_id)
    rows = db.exec(
        select(Membership, User).join(User).where(Membership.household_id == me.household_id).order_by(User.id)
    ).all()
    return {
        "id": me.household_id,
        "name": household.name if household else "",
        "my_role": me.role,
        "members": [
            {"user_id": u.id, "username": u.username, "display_name": u.display_name, "role": m.role} for m, u in rows
        ],
    }


@router.put("/household")
def rename_household(body: HouseholdIn, owner: OwnerDep, db: SessionDep) -> dict:
    household = db.get(Household, owner.household_id)
    assert household  # membership has a foreign key to it
    household.name = body.name.strip()
    db.add(household)
    db.commit()
    return {"id": household.id, "name": household.name}


@router.get("/household/settings")
def get_settings(me: MemberDep, db: SessionDep) -> HouseholdSettings:
    household = db.get(Household, me.household_id)
    assert household
    return household_settings(household)


@router.put("/household/settings")
def save_settings(body: HouseholdSettings, owner: OwnerDep, db: SessionDep) -> HouseholdSettings:
    household = db.get(Household, owner.household_id)
    assert household
    household.settings = body.model_dump()
    db.add(household)
    db.commit()
    return body


@router.get("/household/data-sources")
def data_sources(me: MemberDep, db: SessionDep) -> list[dict]:
    household = db.get(Household, me.household_id)
    assert household
    switches = household_settings(household).model_dump()
    sources = [s | {"enabled": switches.get(s["switch"], True) if s["switch"] else True} for s in DATA_SOURCES]
    cfg = ai.config(household.ai)
    if ai.enabled(cfg):
        names = {
            "anthropic": "Anthropic API",
            "openai": "OpenAI API",
            "openrouter": "OpenRouter",
            "ollama": "Ollama (your own server)",
        }
        sources.append(
            {
                "id": "ai",
                "name": names.get(cfg["provider"], "OpenAI-compatible API"),
                "url": cfg["base_url"],
                "sends": "Your question, plus the garden's place, soil, plantings and open jobs",
                "when": "Only when someone asks the garden assistant"
                + ("" if cfg["provider"] == "ollama" else " (leaves your server)"),
                "used_for": "Answers in Ask",
                "licence": "Provider terms",
                "switch": None,
            }
        )
    return sources


@router.put("/household/members/{user_id}")
def change_role(user_id: int, body: RoleIn, owner: OwnerDep, db: SessionDep) -> dict:
    membership = _member(db, owner, user_id)
    if membership.role == "owner" and body.role != "owner" and _owners(db, owner.household_id) == 1:
        raise HTTPException(409, "A household needs at least one owner")
    membership.role = body.role
    db.add(membership)
    db.commit()
    return {"user_id": user_id, "role": membership.role}


@router.delete("/household/members/{user_id}")
def remove_member(user_id: int, owner: OwnerDep, db: SessionDep) -> dict:
    """Removes the member's login entirely: an account only exists to belong to its household."""
    membership = _member(db, owner, user_id)
    if user_id == owner.user_id:
        raise HTTPException(409, "You can't remove yourself")
    user = db.get(User, membership.user_id)
    db.delete(membership)
    if user:
        db.delete(user)
    db.commit()
    return {"ok": True}


@router.post("/household/invites")
def create_invite(body: InviteIn, owner: OwnerDep, db: SessionDep) -> dict:
    token = secrets.token_urlsafe(24)
    invite = Invite(
        token_hash=token_hash(token),
        household_id=owner.household_id,
        role=body.role,
        created_by=owner.user_id,
        expires_at=now() + timedelta(days=INVITE_DAYS),
    )
    db.add(invite)
    db.commit()
    # The token is shown once; only its hash is stored.
    return {"id": invite.token_hash, "token": token, "path": f"/invite/{token}", "role": invite.role} | {
        "expires_at": invite.expires_at
    }


@router.get("/household/invites")
def list_invites(owner: OwnerDep, db: SessionDep) -> list[dict]:
    invites = db.exec(
        select(Invite).where(Invite.household_id == owner.household_id, Invite.used_at.is_(None))  # type: ignore[union-attr]
    ).all()
    return [
        {"id": i.token_hash, "role": i.role, "created_at": i.created_at, "expires_at": i.expires_at}
        for i in invites
        if i.expires_at > now()
    ]


@router.delete("/household/invites/{invite_id}")
def revoke_invite(invite_id: str, owner: OwnerDep, db: SessionDep) -> dict:
    invite = db.get(Invite, invite_id)
    if not invite or invite.household_id != owner.household_id:
        raise HTTPException(404, "No such invite")
    db.delete(invite)
    db.commit()
    return {"ok": True}


@router.get("/invites/{token}")
def invite_info(token: str, db: SessionDep) -> dict:
    """Public: what an invite link joins, shown before the person signs up."""
    invite = valid_invite(db, token)
    household = db.get(Household, invite.household_id) if invite else None
    if not invite or not household:
        raise HTTPException(404, "This invite link has expired or was already used")
    return {"household": household.name, "role": invite.role, "expires_at": invite.expires_at}
