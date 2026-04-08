from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from history_store import get_match_key, load_history
from strategy_engine import decide_strategy, enrich_match_state


def _parse_target_range(target_runs: Optional[str]) -> Tuple[int, int]:
    if not target_runs:
        return 0, 0

    range_match = re.search(r"(\d+)\s*-\s*(\d+)", target_runs)
    if range_match:
        return int(range_match.group(1)), int(range_match.group(2))

    single_match = re.search(r"(\d+)", target_runs)
    if single_match:
        value = int(single_match.group(1))
        return value, value

    return 0, 0


def _build_objective(state: Dict[str, Any]) -> str:
    batting_team = state.get("batting_team", "batting side")
    bowling_team = state.get("bowling_team", "bowling side")
    total_overs = int(state.get("total_overs") or 20)
    match_note = f" in this rain-shortened {total_overs}-over game" if total_overs != 20 else ""
    if state.get("is_pre_match"):
        return f"Prepare a toss-aware opening plan for {batting_team} and {bowling_team} before the first ball{match_note}, with rain conditions in mind."
    if state.get("target") is not None:
        runs_needed = state.get("runs_needed", "?")
        balls_left = state.get("balls_left", "?")
        return f"Maximize {batting_team}'s chase success by optimizing the next over and managing risk{match_note}. ({runs_needed} needed from {balls_left} balls)"

    phase = state.get("phase")
    if phase == "powerplay":
        return f"Exploit field restrictions for {batting_team}{match_note} without losing control of the innings."
    if phase == "death":
        return f"Maximize finishing output for {batting_team}{match_note} while protecting batting depth."
    return f"Build a strong platform for {batting_team}{match_note} and prepare for the final overs."


def _build_observation_summary(state: Dict[str, Any]) -> str:
    context_text = f" Match context: {state['match_context']}." if state.get("match_context") else ""
    matchup_text = ""
    if state.get("striker") or state.get("bowler"):
        matchup_text = (
            f" Current matchup: {state.get('striker', 'N/A')} {state.get('striker_score', '')} and "
            f"{state.get('non_striker', 'N/A')} {state.get('non_striker_score', '')} versus "
            f"{state.get('bowler', 'N/A')} {state.get('bowler_score', '')}."
        )

    if state.get("is_pre_match"):
        venue_text = f" at {state['venue']}" if state.get("venue") else ""
        status_text = f" Status: {state['status']}." if state.get("status") else ""
        return (
            f"Pre-match state loaded for {state.get('batting_team', 'Unknown')} vs {state.get('bowling_team', 'Unknown')}{venue_text}."
            f" No live score is available yet.{status_text}{context_text}"
        )

    required_rr = state.get("required_run_rate")
    rrr_text = f", required rate {required_rr}" if required_rr is not None else ""
    return (
        f"Observed {state.get('batting_team', 'Unknown')} at {state['runs']}/{state['wickets']} after "
        f"{state['overs']} overs in the {state['phase']} phase, current run rate {state['current_run_rate']}{rrr_text}.{context_text}{matchup_text}"
    )


def _build_memory_summary(history_rows: List[Dict[str, Any]]) -> str:
    if not history_rows:
        return "No saved over memory yet. This is the baseline decision cycle."

    latest = history_rows[-1]
    strategy = latest.get("strategy", "Unknown")
    summary = f"Memory recalls {latest.get('score', 'N/A')} at {latest.get('overs', 'N/A')} overs with strategy '{strategy}'."
    if latest.get("change_reason"):
        summary += f" Last saved insight: {latest['change_reason']}"
    return summary


def _evaluate_last_recommendation(history_rows: List[Dict[str, Any]], current_state: Dict[str, Any]) -> Dict[str, Any]:
    if not history_rows:
        return {
            "status": "baseline",
            "headline": "No prior recommendation to evaluate yet.",
            "detail": "The agent will score both its batting and bowling advice once the next over meaningfully progresses.",
            "batting_status": "baseline",
            "bowling_status": "baseline",
            "batting_headline": "No prior batting recommendation to evaluate yet.",
            "bowling_headline": "No prior bowling recommendation to evaluate yet.",
            "batting_detail": "Waiting for the next completed over.",
            "bowling_detail": "Waiting for the next completed over.",
            "runs_scored": 0,
            "wickets_lost": 0,
            "overs_progress": 0.0,
        }

    previous = history_rows[-1]
    previous_overs = float(previous.get("overs") or 0)
    current_overs = float(current_state.get("overs") or 0)
    overs_progress = current_overs - previous_overs

    if overs_progress < 0.5:
        return {
            "status": "monitoring",
            "headline": "Current over still in progress.",
            "detail": "The agent is still monitoring whether the previous batting and bowling recommendations are playing out.",
            "batting_status": "monitoring",
            "bowling_status": "monitoring",
            "batting_headline": "Batting verdict pending.",
            "bowling_headline": "Bowling verdict pending.",
            "batting_detail": "The over is still live.",
            "bowling_detail": "The over is still live.",
            "runs_scored": 0,
            "wickets_lost": 0,
            "overs_progress": overs_progress,
        }

    runs_scored = int((current_state.get("runs") or 0) - (previous.get("runs") or 0))
    wickets_lost = int((current_state.get("wickets") or 0) - (previous.get("wickets") or 0))
    low_target, high_target = _parse_target_range(previous.get("target_runs"))

    if wickets_lost == 0 and runs_scored > high_target:
        batting_status = "excellent"
        batting_headline = "Batting call outperformed the target."
        batting_detail = f"The batting side scored {runs_scored} runs versus the planned {previous.get('target_runs', 'N/A')} without losing a wicket."
    elif wickets_lost == 0 and low_target <= runs_scored <= high_target:
        batting_status = "on-track"
        batting_headline = "Batting call landed on target."
        batting_detail = f"The previous plan asked for {previous.get('target_runs', 'N/A')} and the batting side delivered {runs_scored} with wickets intact."
    elif wickets_lost > 0 and runs_scored < low_target:
        batting_status = "under-pressure"
        batting_headline = "Batting call struggled under pressure."
        batting_detail = f"Only {runs_scored} runs came in the over and {wickets_lost} wicket(s) fell, so the plan fell short of {previous.get('target_runs', 'N/A')}."
    elif runs_scored < low_target:
        batting_status = "below-target"
        batting_headline = "Batting call was not fully met."
        batting_detail = f"The over produced {runs_scored} runs against a planned {previous.get('target_runs', 'N/A')}, so extra pressure carries forward."
    else:
        batting_status = "mixed"
        batting_headline = "Batting call had a mixed outcome."
        batting_detail = f"The batting side scored {runs_scored} runs with {wickets_lost} wicket(s) lost, so the over brought both progress and risk."

    if wickets_lost >= 1 and runs_scored <= 6:
        bowling_status = "excellent"
        bowling_headline = "Bowling call created scoreboard pressure."
        bowling_detail = f"The bowling side gave away only {runs_scored} and took {wickets_lost} wicket(s), which strongly validates the previous bowling plan."
    elif runs_scored <= 8:
        bowling_status = "on-track"
        bowling_headline = "Bowling call kept control of the over."
        bowling_detail = f"Conceding {runs_scored} runs kept the batting side from breaking away, even if no wicket fell."
    elif runs_scored >= 12 and wickets_lost == 0:
        bowling_status = "under-pressure"
        bowling_headline = "Bowling call was punished."
        bowling_detail = f"The batting side took {runs_scored} runs without losing a wicket, so the bowling matchup or pace mix needs to change immediately."
    elif runs_scored >= 10 and wickets_lost == 0:
        bowling_status = "below-target"
        bowling_headline = "Bowling call leaked momentum."
        bowling_detail = f"The over cost {runs_scored} without a wicket, so the field or bowler type should be adjusted."
    else:
        bowling_status = "mixed"
        bowling_headline = "Bowling call had a mixed outcome."
        bowling_detail = f"The bowling side conceded {runs_scored} and took {wickets_lost} wicket(s), so there were both gains and release balls in the over."

    if batting_status in {"excellent", "on-track"} and bowling_status in {"excellent", "on-track"}:
        status = "strong"
    elif batting_status in {"under-pressure", "below-target"} and bowling_status in {"under-pressure", "below-target"}:
        status = "under-pressure"
    elif batting_status in {"excellent", "on-track"}:
        status = "batting-favored"
    elif bowling_status in {"excellent", "on-track"}:
        status = "bowling-favored"
    else:
        status = "mixed"

    return {
        "status": status,
        "headline": f"Batting: {batting_headline} | Bowling: {bowling_headline}",
        "detail": f"{batting_detail} Bowling view: {bowling_detail}",
        "batting_status": batting_status,
        "bowling_status": bowling_status,
        "batting_headline": batting_headline,
        "bowling_headline": bowling_headline,
        "batting_detail": batting_detail,
        "bowling_detail": bowling_detail,
        "runs_scored": runs_scored,
        "wickets_lost": wickets_lost,
        "overs_progress": overs_progress,
    }


def _reflect_on_previous_advice(evaluation: Dict[str, Any], state: Dict[str, Any], plan: Dict[str, str]) -> Dict[str, str]:
    status = evaluation.get("status", "baseline")
    batting_status = evaluation.get("batting_status", status)
    bowling_status = evaluation.get("bowling_status", status)
    required_rr = state.get("required_run_rate") or 0
    wickets_in_hand = state.get("wickets_in_hand") or 0

    if status == "baseline":
        return {
            "verdict": "Not judged yet",
            "batting_adjustment": "Hold current plan until another over completes",
            "bowling_adjustment": "Hold current field and gather more evidence",
            "reflection": "The reflection agent needs one completed over before it can judge whether the previous batting and bowling advice was correct.",
        }

    if status == "monitoring":
        return {
            "verdict": "Still monitoring",
            "batting_adjustment": "Stay with the present intent for this over",
            "bowling_adjustment": "Stay disciplined until the over finishes",
            "reflection": "The current over is still underway, so the agent is watching both sides before changing aggression levels.",
        }

    if batting_status in {"excellent", "on-track"} and bowling_status in {"excellent", "on-track"}:
        return {
            "verdict": "Yes, for both sides mostly",
            "batting_adjustment": "Stay balanced" if required_rr <= 8 else "Keep controlled aggression",
            "bowling_adjustment": "Keep one wicket-taking option active while protecting the release side",
            "reflection": "Both the batting and bowling calls broadly made sense, so only fine-tuning is needed rather than a full tactical reset.",
        }

    if batting_status in {"excellent", "on-track"} and bowling_status in {"under-pressure", "below-target"}:
        return {
            "verdict": "Batting yes, bowling no",
            "batting_adjustment": "Keep the set batter involved and preserve tempo",
            "bowling_adjustment": "Change bowler type or pace profile immediately",
            "reflection": "The batting read was good, but the bowling side did not execute the right matchup, so that response needs a sharper change.",
        }

    if batting_status in {"under-pressure", "below-target"} and bowling_status in {"excellent", "on-track"}:
        batting_adjustment = "Become more aggressive next over" if wickets_in_hand >= 5 else "Reduce risk for one over to avoid collapse"
        return {
            "verdict": "Batting no, bowling yes",
            "batting_adjustment": batting_adjustment,
            "bowling_adjustment": "Keep pressure on with the same discipline",
            "reflection": "The bowling-side read was stronger than the batting one, so the batting plan needs the bigger adjustment now.",
        }

    if batting_status in {"under-pressure", "below-target"} and bowling_status in {"under-pressure", "below-target"}:
        return {
            "verdict": "Not fully on either side",
            "batting_adjustment": "Reset with clearer strike rotation and one boundary option",
            "bowling_adjustment": "Attack the stumps with a better-suited bowler and tighter boundary protection",
            "reflection": "Neither side got the previous call quite right, so the next recommendation should be more matchup-specific and less generic.",
        }

    return {
        "verdict": "Partly",
        "batting_adjustment": "Use controlled aggression",
        "bowling_adjustment": "Stay balanced with wicket pressure",
        "reflection": "The previous over brought mixed signals, so neither team should overreact; both should make smaller tactical adjustments.",
    }


def _estimate_confidence(state: Dict[str, Any], plan: Dict[str, str]) -> int:
    score = 68

    if state.get("target") is not None:
        required_rr = state.get("required_run_rate") or 0
        current_rr = state.get("current_run_rate") or 0
        wickets_in_hand = state.get("wickets_in_hand") or 0
        score += int(round((current_rr - required_rr) * 3))
        score += (wickets_in_hand - 5) * 2
    else:
        score += 5 if state.get("phase") == "powerplay" else 0
        score -= max((state.get("wickets") or 0) - 2, 0) * 3

    risk_level = (plan.get("risk_level") or "").lower()
    if "high" in risk_level:
        score -= 8
    elif "low" in risk_level:
        score += 4

    return max(35, min(92, int(round(score))))


def _build_action_summary(plan: Dict[str, str]) -> str:
    batting_summary = (
        f"Batting plan: {plan.get('strategy', 'Unknown')} | target {plan.get('target_runs', 'N/A')} runs next over | "
        f"risk {plan.get('risk_level', 'N/A')} | focus: {plan.get('focus', 'N/A')}."
    )
    bowling_summary = (
        f" Bowling response: {plan.get('bowling_strategy', 'Unknown')} | risk {plan.get('bowling_risk_level', 'N/A')} | "
        f"focus: {plan.get('bowling_focus', 'N/A')}."
    )
    awareness = ""
    if plan.get("awareness_notes"):
        awareness = f" Key facts: {' | '.join(plan['awareness_notes'])}."
    return batting_summary + bowling_summary + awareness


def run_agent_cycle(state: Dict[str, Any]) -> Dict[str, Any]:
    enriched_state = enrich_match_state(state)
    plan = decide_strategy(enriched_state)

    match_key = get_match_key(state)
    history_rows = load_history(match_key=match_key, limit=6)

    objective = _build_objective(enriched_state)
    observation = _build_observation_summary(enriched_state)
    memory = _build_memory_summary(history_rows)
    evaluation = _evaluate_last_recommendation(history_rows, enriched_state)
    reflection = _reflect_on_previous_advice(evaluation, enriched_state, plan)
    confidence = _estimate_confidence(enriched_state, plan)
    action_summary = _build_action_summary(plan)

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
        "objective": objective,
        "observation": observation,
        "memory": memory,
        "evaluation": evaluation,
        "reflection": reflection,
        "confidence": confidence,
        "action_summary": action_summary,
        "reasoning_steps": reasoning_steps,
        "match_key": match_key,
    }
