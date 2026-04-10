from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from backend.core.agent_engine import AgentEngine
from backend.core.rule_engine import RuleEngine

logger = logging.getLogger("cricket_agent.strategy_service")
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def _build_request_id(state: Dict[str, Any]) -> str:
    match_id = state.get("match_id") or "manual"
    innings = state.get("innings") or 1
    overs = str(state.get("overs") or 0).replace(".", "-")
    return f"{match_id}-{innings}-{overs}"


def _log(level: int, message: str, **fields: Any) -> None:
    details = " | ".join(f"{key}={value}" for key, value in fields.items() if value is not None)
    logger.log(level, f"{message}{' | ' + details if details else ''}")


def _combine_unique_items(*groups: Optional[list[Any]]) -> list[Any]:
    combined: list[Any] = []
    for group in groups:
        for item in group or []:
            if item and item not in combined:
                combined.append(item)
    return combined


def _merge_plans(rule_plan: Dict[str, Any], agent_plan: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(rule_plan or {})
    merged.update(agent_plan or {})

    for key in (
        "awareness_notes",
        "batting_tactics",
        "bowling_tactics",
        "phase_watchouts",
        "matchup_insights",
        "decision_rationale",
        "avoid_now",
    ):
        combined = _combine_unique_items((rule_plan or {}).get(key), (agent_plan or {}).get(key))
        if combined:
            merged[key] = combined

    return merged


def _build_fallback_output(
    rule_output: Dict[str, Any],
    request_id: str,
    fallback_reason: str,
    rule_ms: float,
    agent_ms: float,
    total_ms: float,
) -> Dict[str, Any]:
    enriched_state = dict(rule_output["state"])
    plan = _merge_plans(rule_output.get("plan", {}), {})

    plan["decision_rationale"] = _combine_unique_items(
        plan.get("decision_rationale"),
        ["Fallback mode kept the deterministic rule-based cricket plan active for this refresh."],
    )

    phase = enriched_state.get("phase", "unknown")
    batting_team = enriched_state.get("batting_team", "Batting side")
    bowling_team = enriched_state.get("bowling_team", "Bowling side")
    scoreline = f"{enriched_state.get('runs', 0)}/{enriched_state.get('wickets', 0)} after {enriched_state.get('overs', 0)} overs"

    observation = f"Fallback observation: {batting_team} are {scoreline} in the {phase} phase against {bowling_team}."
    memory = "Fallback mode skipped the deeper reflective layer, but the deterministic plan is still available."
    evaluation = {
        "status": "fallback",
        "headline": "Rule-engine fallback active.",
        "detail": "The analysis stayed available by switching to the deterministic rule engine for this refresh.",
        "batting_status": "fallback",
        "bowling_status": "fallback",
        "batting_headline": "Batting recommendation preserved.",
        "bowling_headline": "Bowling recommendation preserved.",
        "batting_detail": "Use the current batting plan as the safe next move while the reflective layer recovers.",
        "bowling_detail": "Use the current bowling counter-plan as the safe next move while the reflective layer recovers.",
        "runs_scored": 0,
        "wickets_lost": 0,
        "overs_progress": 0.0,
    }
    reflection = {
        "verdict": "Safe fallback engaged",
        "batting_adjustment": "Keep the core batting plan simple and matchup-aware.",
        "bowling_adjustment": "Keep the bowling plan disciplined until the next clean refresh.",
        "reflection": "The system protected continuity by falling back to the rule engine instead of returning no recommendation.",
    }
    action_summary = (
        f"Fallback active: batting plan {plan.get('strategy', 'Stay balanced')} | "
        f"bowling plan {plan.get('bowling_strategy', 'Stay disciplined')} | "
        f"focus: {plan.get('focus', 'Preserve control and keep the next over clear.')}"
    )
    confidence = max(52, min(82, int(round(enriched_state.get("estimated_win_probability") or 68))))

    reasoning_steps = [
        {"step": "Observe", "detail": observation},
        {"step": "Recall", "detail": memory},
        {"step": "Evaluate", "detail": evaluation["detail"]},
        {"step": "Reflect", "detail": reflection["reflection"]},
        {"step": "Act", "detail": action_summary},
    ]

    return {
        "state": enriched_state,
        "plan": plan,
        "objective": f"Keep a reliable recommendation active for {batting_team} vs {bowling_team} using the rule-engine fallback.",
        "observation": observation,
        "memory": memory,
        "evaluation": evaluation,
        "reflection": reflection,
        "confidence": confidence,
        "action_summary": action_summary,
        "reasoning_steps": reasoning_steps,
        "match_key": rule_output["match_key"],
        "engine_meta": {
            "mode": "rule-fallback",
            "primary_engine": "rule-engine",
            "supporting_engine": None,
            "fallback_used": True,
            "fallback_reason": fallback_reason,
            "request_id": request_id,
            "timings_ms": {
                "rule": rule_ms,
                "agent": agent_ms,
                "total": total_ms,
            },
            "warnings": [
                "Reflective agent processing was unavailable for this refresh, so the rule-based fallback was used.",
            ],
        },
    }


def run_hybrid_analysis(state: Dict[str, Any]) -> Dict[str, Any]:
    request_id = _build_request_id(state)
    started = time.perf_counter()

    rule_output: Optional[Dict[str, Any]] = None
    rule_ms = 0.0
    try:
        rule_started = time.perf_counter()
        rule_output = RuleEngine().analyze(state)
        rule_ms = round((time.perf_counter() - rule_started) * 1000, 2)
        _log(
            logging.INFO,
            "Rule engine evaluation completed",
            request_id=request_id,
            match_key=rule_output.get("match_key"),
            phase=rule_output.get("state", {}).get("phase"),
            ms=rule_ms,
        )
    except Exception as exc:
        rule_ms = round((time.perf_counter() - started) * 1000, 2)
        _log(
            logging.WARNING,
            "Rule engine evaluation failed",
            request_id=request_id,
            error=exc.__class__.__name__,
            detail=str(exc),
            ms=rule_ms,
        )

    try:
        agent_started = time.perf_counter()
        agent_output = AgentEngine().analyze(state)
        agent_ms = round((time.perf_counter() - agent_started) * 1000, 2)
        total_ms = round((time.perf_counter() - started) * 1000, 2)

        merged_output = dict(agent_output)
        if rule_output is not None:
            merged_output["plan"] = _merge_plans(rule_output.get("plan", {}), agent_output.get("plan", {}))
            mode = "hybrid"
            supporting_engine = "rule-engine"
            fallback_used = False
            fallback_reason = None
            warnings: list[str] = []
        else:
            mode = "agent-direct"
            supporting_engine = None
            fallback_used = True
            fallback_reason = "rule_engine_unavailable"
            warnings = ["The hybrid service stayed available through the agent engine after the rule engine was unavailable."]

        merged_output["engine_meta"] = {
            "mode": mode,
            "primary_engine": "agent-engine",
            "supporting_engine": supporting_engine,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "request_id": request_id,
            "timings_ms": {
                "rule": rule_ms,
                "agent": agent_ms,
                "total": total_ms,
            },
            "warnings": warnings,
        }

        _log(
            logging.INFO,
            "Hybrid analysis completed",
            request_id=request_id,
            mode=mode,
            fallback=fallback_used,
            ms=total_ms,
        )
        return merged_output
    except Exception as exc:
        agent_ms = round((time.perf_counter() - started) * 1000, 2) - rule_ms
        total_ms = round((time.perf_counter() - started) * 1000, 2)
        _log(
            logging.WARNING,
            "Agent engine evaluation failed",
            request_id=request_id,
            error=exc.__class__.__name__,
            detail=str(exc),
            ms=agent_ms,
        )
        if rule_output is not None:
            return _build_fallback_output(
                rule_output=rule_output,
                request_id=request_id,
                fallback_reason="agent_engine_unavailable",
                rule_ms=rule_ms,
                agent_ms=max(agent_ms, 0.0),
                total_ms=total_ms,
            )
        raise RuntimeError("Hybrid analysis could not produce a recommendation.") from exc
