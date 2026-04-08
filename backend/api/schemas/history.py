from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class HistoryEntry(BaseModel):
    timestamp: Optional[str] = None
    match_key: Optional[str] = None
    match_id: Optional[str] = None
    batting_team: Optional[str] = None
    bowling_team: Optional[str] = None
    runs: Optional[int] = None
    wickets: Optional[int] = None
    score: Optional[str] = None
    overs: Optional[float] = None
    phase: Optional[str] = None
    total_overs: Optional[float] = None
    win_probability: Optional[float] = None
    win_probability_delta: Optional[float] = None
    strategy: Optional[str] = None
    bowling_strategy: Optional[str] = None
    target_runs: Optional[str] = None
    risk_level: Optional[str] = None
    agent_confidence: Optional[int] = None
    change_reason: Optional[str] = None

    model_config = {"extra": "allow"}


class HistoryResponse(BaseModel):
    match_key: str
    entries: List[Dict[str, Any]]
