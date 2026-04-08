"""AnalysisService — service-manager layer that orchestrates the agent cycle
and history persistence.

Keeps routers thin: they call run_analysis() and get back a structured
result; they don't touch agent_core or history_store directly.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from backend.core.agent_core import run_agent_cycle
from backend.core.history_store import (
    build_history_entry,
    get_match_key,
    load_history,
    save_history_entry,
)
from backend.core.prematch_advisor import build_pre_match_advice


class AnalysisService:
    """Runs the full agent cycle and persists history for a given match state."""

    def run_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        agent_output = run_agent_cycle(state)
        enriched_state = agent_output["state"]
        plan = agent_output["plan"]

        entry = build_history_entry(state, enriched_state, plan, agent_output)
        history_saved = save_history_entry(entry)

        pre_match_advice = build_pre_match_advice(state)

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
            "pre_match_advice": pre_match_advice,
            "history_entry": entry,
            "history_saved": history_saved,
        }

    def get_history(self, match_key: str, limit: int = 50) -> list:
        return load_history(match_key=match_key, limit=limit)

    def get_match_key(self, state: Dict[str, Any]) -> str:
        return get_match_key(state)
