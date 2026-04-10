from __future__ import annotations

import asyncio
from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, Query

from backend.services.auth_service import get_optional_current_user
from backend.services.session_service import fetch_session

router = APIRouter(prefix="/api/session", tags=["session"])


@router.get("/{session_id}")
async def get_session_context(
    session_id: str,
    limit: Annotated[int, Query(ge=1, le=200)] = 30,
    current_user: Annotated[Optional[Dict[str, Any]], Depends(get_optional_current_user)] = None,
) -> Dict[str, Any]:
    return await asyncio.to_thread(
        fetch_session,
        session_id,
        limit,
        current_user.get("id") if current_user else None,
    )
