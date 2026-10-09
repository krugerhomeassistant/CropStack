"""Catalog browsing and household overrides (SPEC §6.1, §16.1, P5)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from .. import catalog as cat
from ..config import get_settings
from ..deps import EditorDep, MemberDep, OwnerDep, SessionDep
from ..models import CatalogOverride, now

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


def load_catalog() -> cat.Catalog:
    settings = get_settings()
    return cat.load(settings.catalog_dir, settings.private_catalog_dir)


def current(request: Request) -> cat.Catalog:
    return request.app.state.catalog


CatalogDep = Annotated[cat.Catalog, Depends(current)]


class OverrideIn(BaseModel):
    path: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9_]+(\.[a-z0-9_]+)*$")
    value: Any


def _overrides(db: Session, household_id: int, kind: str, slug: str) -> dict[str, Any]:
    rows = db.exec(
        select(CatalogOverride).where(
            CatalogOverride.household_id == household_id, CatalogOverride.kind == kind, CatalogOverride.slug == slug
        )
    ).all()
    return {r.path: r.value for r in rows}


def _known(c: cat.Catalog, kind: str, slug: str) -> None:
    if kind not in cat.KINDS or c.get(kind, slug) is None:
        raise HTTPException(404, f"No {kind} {slug!r} in the catalog")


@router.get("")
def status(c: CatalogDep, me: MemberDep) -> dict:
    return {
        "version": c.version,
        "counts": {kind: len(c.list(kind)) for kind in cat.KINDS},
        "private_items": sum(origin != "bundled" for origin in c.origin.values()),
        # Problems in the owner's private pack are shown to them; the bundled catalog is checked in CI.
        "private_errors": c.private_errors if me.role == "owner" else [],
    }


@router.post("/reload")
def reload(request: Request, _: OwnerDep) -> dict:
    """Re-read the catalog (e.g. after editing files in the private pack) without restarting."""
    request.app.state.catalog = load_catalog()
    c: cat.Catalog = request.app.state.catalog
    return {"version": c.version, "items": len(c.items), "private_errors": c.private_errors}


@router.get("/sources")
def sources(c: CatalogDep, _: MemberDep) -> list[dict]:
    """The source registry (catalog/sources.yaml): licence and how each source may be used, for the credits page."""
    return [s.model_dump(mode="json") for s in c.sources.values()]


@router.get("/{kind}")
def list_items(kind: str, c: CatalogDep, _: MemberDep) -> list[dict]:
    if kind not in cat.KINDS:
        raise HTTPException(404, f"Unknown kind {kind!r}")
    return [
        {
            "slug": slug,
            "names": data.get("names", {}),
            "scientific_name": data.get("scientific_name"),
            "family": data.get("family"),
            "origin": c.origin[(kind, slug)],
            "parent": data.get("parent"),
        }
        for slug, data in c.list(kind)
    ]


@router.get("/{kind}/{slug}")
def get_item(kind: str, slug: str, c: CatalogDep, me: MemberDep, db: SessionDep) -> dict:
    _known(c, kind, slug)
    overrides = _overrides(db, me.household_id, kind, slug)
    return {
        "data": cat.effective(c, kind, slug, overrides),
        "origin": c.origin[(kind, slug)],
        "overrides": overrides,
        "sources": {ref: c.sources[ref].model_dump(mode="json") for ref in _refs(c, kind, slug) if ref in c.sources},
    }


def _refs(c: cat.Catalog, kind: str, slug: str) -> set[str]:
    data = cat.effective(c, kind, slug) or {}
    return {ref for ref in cat._source_refs(data) if ref}


@router.put("/{kind}/{slug}/overrides")
def set_override(kind: str, slug: str, body: OverrideIn, c: CatalogDep, me: EditorDep, db: SessionDep) -> dict:
    _known(c, kind, slug)
    try:
        cat.check_overrides(c, kind, slug, _overrides(db, me.household_id, kind, slug) | {body.path: body.value})
    except cat.CatalogError as e:
        raise HTTPException(422, str(e)) from e
    row = db.get(CatalogOverride, (me.household_id, kind, slug, body.path)) or CatalogOverride(
        household_id=me.household_id, kind=kind, slug=slug, path=body.path, value=body.value
    )
    row.value, row.updated_at = body.value, now()
    db.add(row)
    db.commit()
    return {"path": body.path, "value": body.value}


@router.delete("/{kind}/{slug}/overrides")
def reset_override(kind: str, slug: str, c: CatalogDep, me: EditorDep, db: SessionDep, path: str = Query()) -> dict:
    """Back to the catalog value."""
    _known(c, kind, slug)
    row = db.get(CatalogOverride, (me.household_id, kind, slug, path))
    if row:
        db.delete(row)
        db.commit()
    return {"ok": True}
