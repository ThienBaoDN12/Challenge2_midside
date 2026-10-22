"""TrustGate AI backend — FastAPI entry point.

Run:  uvicorn app.main:app --reload   (from the backend/ folder)
Docs: http://localhost:8000/docs
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .config import DATA_DIR, settings
from .errors import ApiError, api_error_handler
from .routers import accounts, connections, contracts, listings, rooms
from .seed import seed
from .services import ratelimit


@asynccontextmanager
async def lifespan(_: FastAPI):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db.init_schema()
    seed()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        title="TrustGate AI API",
        version="2.0.0",
        description="SRS v2 · T/H1: seller listing → buyer AI discovery → connection → deal room → contract.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(ApiError, api_error_handler)
    for r in (accounts, listings, connections, rooms, contracts):
        app.include_router(r.router)

    @app.get("/api/health")
    def health():
        return {"ok": True}

    @app.post("/api/demo/reset")
    def reset_demo():
        """Wipe and reseed the demo database (disable with TRUSTGATE_DEMO=0)."""
        if os.getenv("TRUSTGATE_DEMO", "1") != "1":
            raise ApiError("forbidden", "Chế độ demo đang tắt.")
        conn = db.get_conn()
        tables = [r["name"] for r in db.all_("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
        for t in tables:
            conn.execute(f"DROP TABLE {t}")
        conn.commit()
        db.init_schema()
        seed()
        ratelimit.reset()
        return {"ok": True}

    return app


app = create_app()
