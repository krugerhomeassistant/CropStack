"""FastAPI app factory: API under /api, the built PWA served for every other path."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from . import VERSION
from .config import get_settings
from .db import get_engine, init_db
from .routers import auth, garden


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


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

    for router in (auth.router, garden.router):
        app.include_router(router)

    @app.get("/api/health", tags=["system"])
    def health() -> dict[str, str]:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "version": VERSION}

    static: Path = settings.static_dir
    if static.is_dir():

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str) -> FileResponse:
            if path.startswith("api/"):
                raise HTTPException(404)
            file = (static / path).resolve()
            # Serve real files inside the build dir; everything else is a client-side route.
            if file.is_file() and file.is_relative_to(static.resolve()):
                return FileResponse(file)
            return FileResponse(static / "index.html")

    return app


app = create_app()
