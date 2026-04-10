from __future__ import annotations

from typing import Annotated, Any, Dict

from fastapi import APIRouter, Query

from backend.services.session_service import fetch_session

router = APIRouter(prefix="/api/session", tags=["session"])


@router.get("/{session_id}")
def get_session_context(
    session_id: str,
    limit: Annotated[int, Query(ge=1, le=200)] = 30,
) -> Dict[str, Any]:
    return fetch_session(session_id=session_id, limit=limit)
