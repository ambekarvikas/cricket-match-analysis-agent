from __future__ import annotations

import asyncio
from typing import Annotated, Any, Dict

from fastapi import APIRouter, Query

from backend.api.schemas.history import HistoryResponse
from backend.services.history_service import fetch_history

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/{match_key}", response_model=HistoryResponse)
async def get_history(
    match_key: str,
    limit: Annotated[int, Query(default=50, ge=1, le=200)] = 50,
) -> Dict[str, Any]:
    entries = await asyncio.to_thread(fetch_history, match_key=match_key, limit=limit)
    return {"match_key": match_key, "entries": entries}
