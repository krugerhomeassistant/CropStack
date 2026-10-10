"""FastAPI app factory: API under /api, the built PWA served for every other path."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from . import VERSION, scheduler
from .config import get_settings
from .db import get_engine, init_db
from .routers import (
    ai,
    auth,
    beds,
    calendar,
    catalog,
    garden,
    household,
    pantry,
    plan,
    plantings,
    recommend,
    today,
    weather,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    app.state.catalog = catalog.load_catalog()  # a broken bundled catalog stops start-up; CI catches it first
    jobs = asyncio.create_task(scheduler.run_forever()) if get_settings().scheduler else None
    yield
    if jobs:
        jobs.cancel()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="CropStack", version=VERSION, lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json"
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.resolved_secret(),
        session_cookie="cropstack_session",
        max_age=settings.session_max_age_days * 86400,
        same_site="lax",
        https_only=settings.secure_cookies,
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next) -> Response:
        resp = await call_next(request)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        if request.url.path.startswith("/api/"):
            resp.headers.setdefault("Cache-Control", "no-store")
        return resp

    for router in (
        auth.router,
        garden.router,
        household.router,
        catalog.router,
        beds.router,
        ai.router,
        calendar.router,
        recommend.router,
        plan.router,
        pantry.router,
        plantings.router,
        today.router,
        weather.router,
    ):
        app.include_router(router)

    @app.get("/api/health", tags=["system"])
    def health() -> dict:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "version": VERSION, "jobs": scheduler.status()}

    static: Path = settings.static_dir
    if static.is_dir():

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str) -> FileResponse:
            if path.startswith("api/"):
                raise HTTPException(404)
            file = (static / path).resolve()
            # Serve real files inside the build dir; everything else is a client-side route.
            if file.is_file() and file.is_relative_to(static.resolve()):
                # Built assets have hashed names and never change; the page, worker and manifest must be re-checked
                # on every visit or an installed app keeps showing the old screens.
                hashed = path.startswith("assets/")
                return FileResponse(
                    file, headers={"Cache-Control": "public, max-age=31536000, immutable" if hashed else "no-cache"}
                )
            return FileResponse(static / "index.html", headers={"Cache-Control": "no-cache"})

    return app


app = create_app()
