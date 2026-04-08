from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.core.data_source import (
    SAMPLE_MATCHES,
    get_hardcoded_match_state,
    get_live_match_state_from_cricbuzz,
    list_live_matches_from_cricbuzz,
)


def list_scenarios() -> List[str]:
    return list(SAMPLE_MATCHES.keys())


def get_scenario_state(name: str) -> Dict[str, Any]:
    return get_hardcoded_match_state(name)


def list_live_matches(series_hint: Optional[str] = None) -> List[Dict[str, Any]]:
    return list_live_matches_from_cricbuzz(series_hint=series_hint)


def get_live_match(match_reference: Optional[str] = None) -> Dict[str, Any]:
    return get_live_match_state_from_cricbuzz(match_reference)
