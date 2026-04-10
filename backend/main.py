from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import analysis, history, matches, session

app = FastAPI(
    title="Cricket Match Analysis Agent API",
    description="FastAPI backend for live cricket strategy analysis.",
    version="1.0.0",
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
app.include_router(session.router)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
