from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend.api.schemas.analysis import AnalysisRequest, AnalysisResponse, PreMatchResponse
from backend.services.match_service import get_prematch_advice, run_analysis

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/run", response_model=AnalysisResponse)
def run_analysis_endpoint(request: AnalysisRequest) -> Dict[str, Any]:
    try:
        return run_analysis(request.state.model_dump(), session_id=request.session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/prematch", response_model=PreMatchResponse)
def prematch_endpoint(request: AnalysisRequest) -> Dict[str, Any]:
    try:
        return get_prematch_advice(request.state.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
