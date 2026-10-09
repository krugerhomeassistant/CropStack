"""Shared FastAPI dependencies and password hashing."""

from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, Request
from sqlmodel import Session

from .db import get_session
from .models import User

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
