from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Query

from backend.api.schemas.history import HistoryResponse
from backend.services.history_service import fetch_history

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/{match_key}", response_model=HistoryResponse)
def get_history(match_key: str, limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    entries = fetch_history(match_key=match_key, limit=limit)
    return {"match_key": match_key, "entries": entries}
