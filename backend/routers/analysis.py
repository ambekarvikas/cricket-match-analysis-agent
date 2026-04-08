"""Router: /api/analysis — run the full agent cycle on a match state."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.analysis_service import AnalysisService

router = APIRouter(prefix="/api/analysis", tags=["analysis"])
_service = AnalysisService()


class MatchStateInput(BaseModel):
    """Minimal required fields to describe a match state for analysis."""

    batting_team: str = Field(..., example="India")
    bowling_team: str = Field(..., example="Australia")
    runs: int = Field(..., example=140)
    wickets: int = Field(..., example=4)
    overs: float = Field(..., example=15.0)
    innings: int = Field(1, example=2)
    target: Optional[int] = Field(None, example=180)
    total_overs: Optional[float] = Field(None, example=20.0)
    match_id: Optional[str] = Field(None)
    venue: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    source_url: Optional[str] = Field(None)
    striker: Optional[str] = Field(None)
    non_striker: Optional[str] = Field(None)
    bowler: Optional[str] = Field(None)
    striker_score: Optional[str] = Field(None)
    non_striker_score: Optional[str] = Field(None)
    bowler_score: Optional[str] = Field(None)
    is_pre_match: Optional[bool] = Field(None)
    conditions_note: Optional[str] = Field(None)
    match_context: Optional[str] = Field(None)

    model_config = {"extra": "allow"}


@router.post("/", summary="Run the full agent analysis cycle on a match state")
def run_analysis(payload: MatchStateInput) -> Dict[str, Any]:
    state = payload.model_dump(exclude_none=True)
    try:
        return _service.run_analysis(state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
