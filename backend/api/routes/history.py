from __future__ import annotations

import asyncio
from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, Query

from backend.api.schemas.history import HistoryResponse
from backend.services.auth_service import get_optional_current_user
from backend.services.history_service import fetch_history

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/{match_key}", response_model=HistoryResponse)
async def get_history(
    match_key: str,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    current_user: Annotated[Optional[Dict[str, Any]], Depends(get_optional_current_user)] = None,
) -> Dict[str, Any]:
    entries = await asyncio.to_thread(
        fetch_history,
        match_key,
        limit,
        current_user.get("id") if current_user else None,
    )
    return {"match_key": match_key, "entries": entries}
