from __future__ import annotations

import asyncio
import logging
from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.api.schemas.analysis import AnalysisRequest, AnalysisResponse, PreMatchResponse
from backend.services.auth_service import get_optional_current_user
from backend.services.match_service import get_prematch_advice, run_analysis

logger = logging.getLogger("cricket_agent.api.analysis")

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post(
    "/run",
    response_model=AnalysisResponse,
    responses={500: {"description": "Analysis request failed."}},
)
async def run_analysis_endpoint(
    request: AnalysisRequest,
    current_user: Annotated[Optional[Dict[str, Any]], Depends(get_optional_current_user)] = None,
) -> Dict[str, Any]:
    try:
        return await asyncio.to_thread(
            run_analysis,
            request.state.model_dump(),
            request.session_id,
            current_user.get("id") if current_user else None,
        )
    except Exception as exc:
        logger.exception("Analysis endpoint failed")
        raise HTTPException(status_code=500, detail="Analysis request failed.") from exc


@router.post(
    "/prematch",
    response_model=PreMatchResponse,
    responses={500: {"description": "Pre-match analysis failed."}},
)
async def prematch_endpoint(request: AnalysisRequest) -> Dict[str, Any]:
    try:
        return await asyncio.to_thread(get_prematch_advice, request.state.model_dump())
    except Exception as exc:
        logger.exception("Pre-match endpoint failed")
        raise HTTPException(status_code=500, detail="Pre-match analysis failed.") from exc
