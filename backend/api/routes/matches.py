from __future__ import annotations

import asyncio
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.services.data_service import get_live_match, get_scenario_state, list_scenarios
from backend.services.live_refresh_service import live_refresh_service

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("/scenarios")
async def get_scenarios() -> List[str]:
    return list_scenarios()


@router.get("/scenario/{name}", responses={404: {"description": "Scenario not found."}})
async def get_scenario(name: str) -> Dict[str, Any]:
    try:
        return await asyncio.to_thread(get_scenario_state, name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/live", responses={502: {"description": "Live data source unavailable."}})
async def get_live_matches(
    series_hint: Annotated[Optional[str], Query()] = None,
) -> List[Dict[str, Any]]:
    try:
        return await live_refresh_service.get_matches(series_hint=series_hint)
    except ConnectionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/live/{match_reference:path}", responses={404: {"description": "Live match not found."}})
async def get_live_match_by_reference(match_reference: str) -> Dict[str, Any]:
    try:
        return await asyncio.to_thread(get_live_match, match_reference)
    except (ValueError, ConnectionError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
