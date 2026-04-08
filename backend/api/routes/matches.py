from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.api.schemas.match import LiveMatchSummary, MatchState
from backend.services.data_service import (
    get_live_match,
    get_scenario_state,
    list_live_matches,
    list_scenarios,
)

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("/scenarios", response_model=List[str])
def get_scenarios() -> List[str]:
    return list_scenarios()


@router.get("/scenario/{name}", response_model=Dict[str, Any])
def get_scenario(name: str) -> Dict[str, Any]:
    try:
        return get_scenario_state(name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/live", response_model=List[Dict[str, Any]])
def get_live_matches(series_hint: Optional[str] = Query(default=None)) -> List[Dict[str, Any]]:
    try:
        return list_live_matches(series_hint=series_hint)
    except ConnectionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/live/{match_reference:path}", response_model=Dict[str, Any])
def get_live_match_by_reference(match_reference: str) -> Dict[str, Any]:
    try:
        return get_live_match(match_reference)
    except (ValueError, ConnectionError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
