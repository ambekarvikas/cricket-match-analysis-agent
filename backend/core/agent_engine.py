from __future__ import annotations

from typing import Any, Dict

from backend.core.agent_core import run_agent_cycle


class AgentEngine:
    """Reflective engine that adds observation, memory, evaluation, and action synthesis."""

    name = "agent-engine"

    def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        result = run_agent_cycle(state)
        engine_meta = dict(result.get("engine_meta") or {})
        engine_meta.update(
            {
                "mode": "agent-only",
                "primary_engine": self.name,
                "fallback_used": False,
            }
        )
        result["engine_meta"] = engine_meta
        return result


def run_agent_engine(state: Dict[str, Any]) -> Dict[str, Any]:
    return AgentEngine().analyze(state)
