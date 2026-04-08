"""Router: /api/matches — list live matches and hardcoded scenarios."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.services.match_service import MatchService

router = APIRouter(prefix="/api/matches", tags=["matches"])
_service = MatchService()


@router.get("/scenarios", summary="List available hardcoded scenario names")
def list_scenarios() -> List[str]:
    return _service.list_scenarios()


@router.get("/scenarios/{name}", summary="Get state for a named hardcoded scenario")
def get_scenario(name: str) -> Dict[str, Any]:
    try:
        return _service.get_scenario_state(name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/live", summary="List currently detected live matches from Cricbuzz")
def list_live_matches(
    refresh: bool = Query(False, description="Force a cache refresh"),
) -> List[Dict[str, Any]]:
    try:
        return _service.list_live_matches(force_refresh=refresh)
    except ConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/live/state", summary="Fetch live match state from Cricbuzz")
def get_live_state(
    ref: Optional[str] = Query(None, description="Match URL, match_id, or team name"),
    refresh: bool = Query(False, description="Force a cache refresh"),
) -> Dict[str, Any]:
    try:
        return _service.get_live_match_state(match_reference=ref, force_refresh=refresh)
    except (ConnectionError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
