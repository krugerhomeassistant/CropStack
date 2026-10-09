"""The household: its name, members and roles, and invite links for new members."""

import secrets
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, func, select

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
