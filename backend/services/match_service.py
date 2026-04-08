from __future__ import annotations

from typing import Any, Dict, Optional

from backend.core.agent_core import run_agent_cycle
from backend.core.history_store import build_history_entry, get_match_key
from backend.core.prematch_advisor import build_pre_match_advice
from backend.services.data_service import get_live_match, get_scenario_state
from backend.services.history_service import persist_entry


def run_analysis(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the agent cycle and persist a history entry. Returns a combined response."""
    agent_output = run_agent_cycle(state)
    enriched_state = agent_output["state"]
    plan = agent_output["plan"]
    entry = build_history_entry(state, enriched_state, plan, agent_output)
    history_saved = persist_entry(entry)
    return {
        "match_key": agent_output["match_key"],
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
        "history_entry": entry,
        "history_saved": history_saved,
    }


def get_prematch_advice(state: Dict[str, Any]) -> Dict[str, Any]:
    return build_pre_match_advice(state)


def load_live_and_analyze(match_reference: Optional[str] = None) -> Dict[str, Any]:
    state = get_live_match(match_reference)
    return run_analysis(state)


def load_scenario_and_analyze(name: str) -> Dict[str, Any]:
    state = get_scenario_state(name)
    return run_analysis(state)
