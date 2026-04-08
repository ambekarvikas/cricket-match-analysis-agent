from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from backend.api.schemas.match import MatchState


class ReasoningStep(BaseModel):
    step: str
    detail: str


class EvaluationResult(BaseModel):
    status: str
    headline: str
    detail: str
    batting_status: Optional[str] = None
    bowling_status: Optional[str] = None
    batting_headline: Optional[str] = None
    bowling_headline: Optional[str] = None
    batting_detail: Optional[str] = None
    bowling_detail: Optional[str] = None
    runs_scored: Optional[int] = None
    wickets_lost: Optional[int] = None
    overs_progress: Optional[float] = None


class ReflectionResult(BaseModel):
    verdict: str
    batting_adjustment: str
    bowling_adjustment: str
    reflection: str


class StrategyPlan(BaseModel):
    strategy: str
    target_runs: Optional[str] = None
    risk_level: Optional[str] = None
    focus: Optional[str] = None
    bowling_strategy: Optional[str] = None
    bowling_risk_level: Optional[str] = None
    bowling_focus: Optional[str] = None
    awareness_notes: Optional[List[str]] = None


class AnalysisResponse(BaseModel):
    match_key: str
    state: Dict[str, Any]
    plan: Dict[str, Any]
    objective: str
    observation: str
    memory: str
    evaluation: Dict[str, Any]
    reflection: Dict[str, Any]
    confidence: int
    action_summary: str
    reasoning_steps: List[Dict[str, str]]
    history_entry: Dict[str, Any]
    history_saved: bool


class AnalysisRequest(BaseModel):
    state: MatchState


class TossRecommendation(BaseModel):
    decision: str
    confidence: str
    summary: str
    reasons: List[str]


class TeamLineup(BaseModel):
    lineup_type: str
    teams: Dict[str, List[str]]
    source_url: Optional[str] = None


class RecommendedXI(BaseModel):
    lineup_type: str
    teams: Dict[str, List[str]]
    reasoning: List[str]
    comparison_notes: Dict[str, List[str]]


class PreMatchResponse(BaseModel):
    toss: Dict[str, Any]
    recommended_xi: Dict[str, Any]
    lineup: Dict[str, Any]
