from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class MatchState(BaseModel):
    batting_team: Optional[str] = None
    bowling_team: Optional[str] = None
    innings: Optional[int] = None
    runs: int = 0
    wickets: int = 0
    overs: float = 0.0
    target: Optional[int] = None
    total_overs: Optional[float] = None
    match_id: Optional[str] = None
    venue: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    is_pre_match: Optional[bool] = None
    striker: Optional[str] = None
    striker_score: Optional[str] = None
    non_striker: Optional[str] = None
    non_striker_score: Optional[str] = None
    bowler: Optional[str] = None
    bowler_score: Optional[str] = None
    conditions_note: Optional[str] = None
    match_context: Optional[str] = None
    match_description: Optional[str] = None

    model_config = {"extra": "allow"}


class LiveMatchSummary(BaseModel):
    match_id: Optional[str] = None
    batting_team: Optional[str] = None
    bowling_team: Optional[str] = None
    runs: int = 0
    wickets: int = 0
    overs: float = 0.0
    target: Optional[int] = None
    venue: Optional[str] = None
    status: Optional[str] = None
    source_url: Optional[str] = None

    model_config = {"extra": "allow"}
