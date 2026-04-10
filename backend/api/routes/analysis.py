from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend.api.schemas.analysis import AnalysisRequest, AnalysisResponse, PreMatchResponse
from backend.services.match_service import get_prematch_advice, run_analysis

logger = logging.getLogger("cricket_agent.api.analysis")

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/run", response_model=AnalysisResponse)
def run_analysis_endpoint(request: AnalysisRequest) -> Dict[str, Any]:
    try:
        return run_analysis(request.state.model_dump(), session_id=request.session_id)
    except Exception as exc:
        logger.exception("Analysis endpoint failed")
        raise HTTPException(status_code=500, detail="Analysis request failed.") from exc


@router.post("/prematch", response_model=PreMatchResponse)
def prematch_endpoint(request: AnalysisRequest) -> Dict[str, Any]:
    try:
        return get_prematch_advice(request.state.model_dump())
    except Exception as exc:
        logger.exception("Pre-match endpoint failed")
        raise HTTPException(status_code=500, detail="Pre-match analysis failed.") from exc
