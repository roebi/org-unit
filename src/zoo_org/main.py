from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from zoo_org.database import DB_PATH, init_db
from zoo_org.routers import assignments, org_units, persons

STATIC_DIR = Path("/app/static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(DB_PATH)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Zoo Org",
        description="Organizational structure of a zoo",
        version="0.1.0",
        lifespan=lifespan,
    )

    # NFR-08: localhost origins only - no wildcard
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type"],
    )

    # Single app with prefixed routers - keeps DI working in tests
    app.include_router(org_units.router, prefix="/api/v1")
    app.include_router(persons.router, prefix="/api/v1")
    app.include_router(assignments.router, prefix="/api/v1")

    # FR-33: serve GUI at root
    @app.get("/", include_in_schema=False)
    async def serve_gui():
        return FileResponse(STATIC_DIR / "index.html")

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return app


app = create_app()
