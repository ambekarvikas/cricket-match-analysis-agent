"""Router: /api/history — query per-match strategy history."""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Query

from backend.services.analysis_service import AnalysisService

router = APIRouter(prefix="/api/history", tags=["history"])
_service = AnalysisService()


@router.get("/{match_key}", summary="Get saved strategy history for a match")
def get_history(
    match_key: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum number of rows to return"),
) -> List[Dict[str, Any]]:
    return _service.get_history(match_key=match_key, limit=limit)
