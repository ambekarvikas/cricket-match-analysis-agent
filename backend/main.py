"""Cricket Match Analysis Agent — FastAPI application entry point.

Architecture:
  backend/core/     — pure agent & domain logic (strategy, data, history)
  backend/services/ — service-manager layer (orchestration, caching)
  backend/routers/  — thin HTTP route handlers
  frontend/         — React UI that consumes these endpoints

Run locally:
    uvicorn backend.main:app --reload --port 8000
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routers import analysis, history, matches

_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

app = FastAPI(
    title="Cricket Match Analysis Agent",
    description="API-driven cricket analysis powered by a rule-based agent loop.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(matches.router)
app.include_router(analysis.router)
app.include_router(history.router)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}


# Serve the compiled React app when the dist folder exists.
if _FRONTEND_DIST.exists():
    from fastapi.responses import FileResponse

    @app.get("/", include_in_schema=False)
    def serve_spa() -> FileResponse:
        return FileResponse(_FRONTEND_DIST / "index.html")

    app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="static")
else:
    @app.get("/", tags=["health"])
    def root() -> dict:
        return {"status": "ok", "service": "cricket-match-analysis-agent"}
