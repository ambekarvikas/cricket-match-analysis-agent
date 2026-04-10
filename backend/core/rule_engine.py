from __future__ import annotations

from typing import Any, Dict

from backend.core.history_store import get_match_key
from backend.core.strategy_engine import decide_strategy, enrich_match_state


class RuleEngine:
    """Deterministic engine that always returns a safe cricket plan."""

    name = "rule-engine"

    def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        enriched_state = enrich_match_state(state)
        plan = decide_strategy(enriched_state)
        return {
            "engine": self.name,
            "match_key": get_match_key(state),
            "state": enriched_state,
            "plan": plan,
        }


def run_rule_engine(state: Dict[str, Any]) -> Dict[str, Any]:
    return RuleEngine().analyze(state)
