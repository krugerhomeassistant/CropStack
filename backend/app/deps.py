"""Shared FastAPI dependencies and password hashing."""

from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, Request
from sqlmodel import Session

from .db import get_session
from .models import Membership, User

_hasher = PasswordHasher()
SessionDep = Annotated[Session, Depends(get_session)]


def hash_pw(password: str) -> str:
    return _hasher.hash(password)


def verify_pw(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def current_user(request: Request, db: SessionDep) -> User:
    uid = request.session.get("uid")
    user = db.get(User, uid) if uid else None
    if not user:
        raise HTTPException(401, "Not authenticated")
    return user


UserDep = Annotated[User, Depends(current_user)]


def current_member(user: UserDep, db: SessionDep) -> Membership:
    membership = db.get(Membership, user.id)
    if not membership:  # every account is created with a household (register / invite)
        raise HTTPException(403, "Not a member of any household")
    return membership


MemberDep = Annotated[Membership, Depends(current_member)]


def require_role(*roles: str):
    def check(member: MemberDep) -> Membership:
        if member.role not in roles:
            raise HTTPException(403, f"Needs role: {' or '.join(roles)}")
        return member

    return Depends(check)


OwnerDep = Annotated[Membership, require_role("owner")]
EditorDep = Annotated[Membership, require_role("owner", "member")]  # may plan, log and complete tasks
