"""Accounts: register, login, logout, current user, password change."""

import time
from collections import defaultdict, deque

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session, func, select

from ..config import get_settings
from ..deps import SessionDep, UserDep, hash_pw, verify_pw
from ..models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Credentials(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=8, max_length=256)
    display_name: str = Field("", max_length=64)


class PasswordChange(BaseModel):
    current: str
    new: str = Field(min_length=8, max_length=256)


def registration_open(db: Session) -> bool:
    mode = get_settings().allow_registration.lower()
    if mode in ("true", "false"):
        return mode == "true"
    return db.exec(select(func.count()).select_from(User)).one() == 0  # "auto": only the first account


def public_user(user: User) -> dict:
    return user.model_dump(include={"id", "username", "display_name", "created_at"})


@router.get("/status")
def status(request: Request, db: SessionDep) -> dict:
    return {"registration_open": registration_open(db), "authenticated": bool(request.session.get("uid"))}


@router.post("/register")
def register(body: Credentials, request: Request, db: SessionDep) -> dict:
    if not registration_open(db):
        raise HTTPException(403, "Registration is closed")
    username = body.username.strip().lower()
    if db.exec(select(User).where(User.username == username)).first():
        raise HTTPException(409, "Username taken")
    user = User(username=username, password_hash=hash_pw(body.password), display_name=body.display_name or username)
    db.add(user)
    db.commit()
    db.refresh(user)
    request.session["uid"] = user.id
    return public_user(user)


# shortcut: in-memory per process (one uvicorn worker); resets on restart, fine for brute-force damping.
# Per IP only: a per-username limit would let strangers lock the owner out of an internet-facing instance.
FAILS: dict[str, deque[float]] = defaultdict(deque)
WINDOW_S, MAX_FAILS = 15 * 60, 10


def _throttled(key: str) -> bool:
    now = time.monotonic()
    fails = FAILS[key]
    while fails and now - fails[0] > WINDOW_S:
        fails.popleft()
    return len(fails) >= MAX_FAILS


@router.post("/login")
def login(body: Credentials, request: Request, db: SessionDep) -> dict:
    key = f"ip:{request.client.host if request.client else '?'}"
    if _throttled(key):
        raise HTTPException(429, "Too many failed attempts. Try again in 15 minutes.")
    user = db.exec(select(User).where(User.username == body.username.strip().lower())).first()
    if not user or not verify_pw(user.password_hash, body.password):
        FAILS[key].append(time.monotonic())
        raise HTTPException(401, "Invalid username or password")
    FAILS.pop(key, None)
    request.session["uid"] = user.id
    return public_user(user)


@router.post("/logout")
def logout(request: Request) -> dict:
    request.session.clear()
    return {"ok": True}


@router.get("/me")
def me(user: UserDep) -> dict:
    return public_user(user)


@router.post("/password")
def change_password(body: PasswordChange, user: UserDep, db: SessionDep) -> dict:
    if not verify_pw(user.password_hash, body.current):
        raise HTTPException(400, "Current password is wrong")
    user.password_hash = hash_pw(body.new)
    db.add(user)
    db.commit()
    return {"ok": True}
