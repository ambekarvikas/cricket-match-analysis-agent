from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.middleware.rate_limit import (
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    RateLimitMiddleware,
)
from backend.api.routes import analysis, auth, history, matches, session
from backend.db.database import DATABASE_URL, init_db
from backend.services.live_refresh_service import live_refresh_service


def _get_allowed_origins() -> list[str]:
    configured = os.getenv("ALLOWED_ORIGINS")
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return ["http://localhost:5173", "http://localhost:3000"]


@asynccontextmanager
async def lifespan(_: FastAPI):
    await asyncio.to_thread(init_db)
    await live_refresh_service.start()
    try:
        yield
    finally:
        await live_refresh_service.stop()


app = FastAPI(
    title="Cricket Match Analysis Agent API",
    description="FastAPI backend for live cricket strategy analysis.",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    RateLimitMiddleware,
    requests_per_window=RATE_LIMIT_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(matches.router)
app.include_router(analysis.router)
app.include_router(history.router)
app.include_router(session.router)


@app.get("/health")
async def health_check() -> dict:
    return {
        "status": "ok",
        "service": "cricket-match-analysis-agent",
        "database": {
            "configured": bool(DATABASE_URL),
            "driver": DATABASE_URL.split(":", 1)[0],
        },
        "live_cache": live_refresh_service.status(),
        "rate_limit": {
            "requests": RATE_LIMIT_REQUESTS,
            "window_seconds": RATE_LIMIT_WINDOW_SECONDS,
        },
        "auth": {
            "jwt_enabled": True,
        },
    }
