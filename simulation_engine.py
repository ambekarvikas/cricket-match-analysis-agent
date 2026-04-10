from __future__ import annotations

from typing import Any, Dict, List

from strategy_engine import balls_to_overs, decide_strategy, enrich_match_state, overs_to_balls


def _impact_label(delta: int) -> str:
    if delta >= 10:
        return "high positive"
    if delta >= 4:
        return "positive"
    if delta <= -10:
        return "high negative"
    if delta <= -4:
        return "negative"
    return "neutral"


def _scenario_summary(state: Dict[str, Any], runs_delta: int, wickets_delta: int) -> str:
    if state.get("target") is not None:
        if wickets_delta > 0:
            return "A wicket in the next over would sharply increase chase pressure and reduce flexibility."
        if runs_delta >= 12:
            return "A boundary-heavy over would release pressure immediately and swing momentum back toward the batting side."
        if runs_delta <= 4:
            return "A quiet over would hand control to the bowling side and make the next phase far more urgent."
        return "A steady over keeps the chase alive without forcing panic shots."

    if wickets_delta > 0 and runs_delta <= 6:
        return "A wicket-bearing over would hurt the projected finish and shift control toward the fielding side."
    if runs_delta >= 12:
        return "A strong over would lift the projected total and improve the batting side's defending chances."
    return "A steady over keeps the innings on track but does not fully seize momentum."


def _simulate_state(state: Dict[str, Any], runs_delta: int, wickets_delta: int, label: str) -> Dict[str, Any]:
    enriched = enrich_match_state(state)
    base_probability = int(enriched.get("estimated_win_probability") or 50)
    total_balls = max(int((enriched.get("total_overs") or 20) * 6), 1)
    current_balls = min(int(enriched.get("balls_bowled") or overs_to_balls(enriched.get("overs") or 0)), total_balls)
    next_balls = min(current_balls + 6, total_balls)

    simulated_state = dict(state)
    simulated_state["runs"] = int(state.get("runs") or 0) + runs_delta
    simulated_state["wickets"] = min(int(state.get("wickets") or 0) + wickets_delta, 10)
    simulated_state["overs"] = float(balls_to_overs(next_balls))

    simulated_enriched = enrich_match_state(simulated_state)
    simulated_plan = decide_strategy(simulated_enriched)
    win_probability = int(simulated_enriched.get("estimated_win_probability") or base_probability)
    delta = win_probability - base_probability

    return {
        "label": label,
        "summary": _scenario_summary(enriched, runs_delta, wickets_delta),
        "projected_score": f"{simulated_enriched.get('runs', 0)}/{simulated_enriched.get('wickets', 0)} after {simulated_enriched.get('overs', 0)} ov",
        "win_probability": win_probability,
        "win_probability_delta": delta,
        "impact": _impact_label(delta),
        "recommended_response": simulated_plan.get("strategy"),
        "focus": simulated_plan.get("focus"),
    }


def generate_what_if_scenarios(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    enriched = enrich_match_state(state)

    if enriched.get("is_match_complete"):
        return [
            {
                "label": "Result locked",
                "summary": enriched.get("result_summary") or "Match complete.",
                "projected_score": f"{enriched.get('runs', 0)}/{enriched.get('wickets', 0)} after {enriched.get('overs', 0)} ov",
                "win_probability": enriched.get("estimated_win_probability"),
                "win_probability_delta": 0,
                "impact": "closed",
                "recommended_response": "MATCH COMPLETE",
                "focus": "No further live simulation is needed because the result is already decided.",
            }
        ]

    if enriched.get("is_pre_match"):
        templates = [
            ("Strong start (9 in first over)", 9, 0),
            ("Cautious start (6 in first over)", 6, 0),
            ("Early wicket (4/1 after first over)", 4, 1),
        ]
    elif enriched.get("target") is not None:
        templates = [
            ("Score 12 next over", 12, 0),
            ("Score 8 next over", 8, 0),
            ("Lose 1 wicket next over", 6, 1),
            ("Only 4 next over", 4, 0),
        ]
    else:
        templates = [
            ("Add a 12-run over", 12, 0),
            ("Add a steady 8-run over", 8, 0),
            ("6 runs but lose a wicket", 6, 1),
            ("3-run pressure over", 3, 1),
        ]

    return [_simulate_state(enriched, runs_delta, wickets_delta, label) for label, runs_delta, wickets_delta in templates]
