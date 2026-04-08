"""MatchService — service-manager layer for match data fetching and caching.

Separates data-retrieval concerns from the core agent logic so routers
stay thin and the agent layer has no knowledge of HTTP or caching.
"""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from backend.core.data_source import (
    SAMPLE_MATCHES,
    get_hardcoded_match_state,
    get_live_match_state_from_cricbuzz,
    list_live_matches_from_cricbuzz,
)


_LIVE_CACHE: Dict[str, Any] = {}
_CACHE_LOCK = threading.Lock()
_CACHE_TTL_SECONDS = 15


def _cache_key(match_reference: Optional[str]) -> str:
    return match_reference or "__first__"


def _is_stale(cached_at: float) -> bool:
    return (time.monotonic() - cached_at) > _CACHE_TTL_SECONDS


class MatchService:
    """Orchestrates match-data access with a short-lived in-process cache."""

    def list_scenarios(self) -> List[str]:
        return list(SAMPLE_MATCHES.keys())

    def get_scenario_state(self, name: str) -> Dict[str, Any]:
        return get_hardcoded_match_state(name)

    def list_live_matches(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        with _CACHE_LOCK:
            cache_entry = _LIVE_CACHE.get("live_list")
            if not force_refresh and cache_entry and not _is_stale(cache_entry["cached_at"]):
                return cache_entry["data"]

        matches = list_live_matches_from_cricbuzz()

        with _CACHE_LOCK:
            _LIVE_CACHE["live_list"] = {"data": matches, "cached_at": time.monotonic()}
        return matches

    def get_live_match_state(
        self,
        match_reference: Optional[str] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        key = _cache_key(match_reference)

        with _CACHE_LOCK:
            cache_entry = _LIVE_CACHE.get(key)
            if not force_refresh and cache_entry and not _is_stale(cache_entry["cached_at"]):
                return cache_entry["data"]

        state = get_live_match_state_from_cricbuzz(match_reference)

        with _CACHE_LOCK:
            _LIVE_CACHE[key] = {"data": state, "cached_at": time.monotonic()}
        return state
