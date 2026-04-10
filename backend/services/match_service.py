from __future__ import annotations

import copy
import json
import logging
import time
from typing import Any, Dict, Optional

from backend.core.history_store import build_history_entry
from backend.core.prematch_advisor import build_pre_match_advice
from backend.core.simulation_engine import generate_what_if_scenarios
from backend.services.data_service import get_live_match, get_scenario_state
from backend.services.history_service import persist_entry
from backend.services.session_service import fetch_session, persist_session_snapshot, resolve_session_id
from backend.services.strategy_service import run_hybrid_analysis

logger = logging.getLogger("cricket_agent.match_service")

CACHE_TTL_SECONDS = 15
_ANALYSIS_CACHE: Dict[str, Dict[str, Any]] = {}


def _build_state_cache_key(state: Dict[str, Any]) -> str:
    key_fields = {
        "match_id": state.get("match_id"),
        "batting_team": state.get("batting_team"),
        "bowling_team": state.get("bowling_team"),
        "innings": state.get("innings"),
        "runs": state.get("runs"),
        "wickets": state.get("wickets"),
        "overs": state.get("overs"),
        "target": state.get("target"),
        "total_overs": state.get("total_overs"),
        "status": state.get("status"),
        "striker": state.get("striker"),
        "bowler": state.get("bowler"),
    }
    return json.dumps(key_fields, sort_keys=True, default=str)


def _run_cached_agent_cycle(state: Dict[str, Any]) -> tuple[Dict[str, Any], str]:
    cache_key = _build_state_cache_key(state)
    now = time.time()
    cached = _ANALYSIS_CACHE.get(cache_key)

    if cached and (now - cached["timestamp"]) <= CACHE_TTL_SECONDS:
        return copy.deepcopy(cached["result"]), "hit"

    result = run_hybrid_analysis(state)
    _ANALYSIS_CACHE[cache_key] = {
        "timestamp": now,
        "result": copy.deepcopy(result),
    }
    return result, "miss"


def run_analysis(state: Dict[str, Any], session_id: Optional[str] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Run the hybrid strategy service, cache repeated requests, and persist non-critical artifacts safely."""
    agent_output, cache_status = _run_cached_agent_cycle(state)
    enriched_state = agent_output["state"]
    plan = agent_output["plan"]

    engine_meta = dict(agent_output.get("engine_meta") or {})
    engine_meta["cache_status"] = cache_status
    warnings: list[str] = list(engine_meta.get("warnings") or [])

    try:
        what_if = generate_what_if_scenarios(enriched_state)
    except Exception as exc:
        logger.warning("What-if generation failed | match_key=%s | error=%s", agent_output.get("match_key"), exc)
        what_if = []
        warnings.append("What-if simulation was temporarily unavailable for this refresh.")

    entry = build_history_entry(state, enriched_state, plan, agent_output)
    try:
        history_saved = persist_entry(entry, user_id=user_id)
    except Exception as exc:
        logger.warning("History persistence failed | match_key=%s | error=%s", agent_output.get("match_key"), exc)
        history_saved = False
        warnings.append("History persistence was skipped for this refresh.")

    resolved_session_id = resolve_session_id(agent_output["match_key"], session_id=session_id)
    session_payload: Dict[str, Any] = {"summary": None}
    try:
        persist_session_snapshot(
            session_id=resolved_session_id,
            match_key=agent_output["match_key"],
            state=enriched_state,
            plan=plan,
            what_if=what_if,
            confidence=agent_output["confidence"],
            action_summary=agent_output["action_summary"],
            cache_status=cache_status,
            user_id=user_id,
        )
        session_payload = fetch_session(resolved_session_id, limit=12, user_id=user_id)
    except Exception as exc:
        logger.warning("Session persistence failed | session_id=%s | error=%s", resolved_session_id, exc)
        warnings.append("Session tracking was temporarily unavailable for this refresh.")

    if warnings:
        engine_meta["warnings"] = warnings

    return {
        "match_key": agent_output["match_key"],
        "session_id": resolved_session_id,
        "cache_status": cache_status,
        "session_summary": session_payload.get("summary"),
        "engine_meta": engine_meta,
        "state": enriched_state,
        "plan": plan,
        "objective": agent_output["objective"],
        "observation": agent_output["observation"],
        "memory": agent_output["memory"],
        "evaluation": agent_output["evaluation"],
        "reflection": agent_output["reflection"],
        "confidence": agent_output["confidence"],
        "action_summary": agent_output["action_summary"],
        "reasoning_steps": agent_output["reasoning_steps"],
        "what_if": what_if,
        "history_entry": entry,
        "history_saved": history_saved,
    }


def get_prematch_advice(state: Dict[str, Any]) -> Dict[str, Any]:
    return build_pre_match_advice(state)


def load_live_and_analyze(match_reference: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
    state = get_live_match(match_reference)
    return run_analysis(state, session_id=session_id)


def load_scenario_and_analyze(name: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    state = get_scenario_state(name)
    return run_analysis(state, session_id=session_id)
