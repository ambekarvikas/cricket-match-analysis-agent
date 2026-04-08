from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_HISTORY_PATH = Path(__file__).resolve().parent.parent / "data" / "strategy_history.jsonl"
TRACKED_FIELDS = ("runs", "wickets", "overs", "target")
OVER_BUCKET_FIELD = "over_bucket"


def get_match_key(state: Dict[str, Any]) -> str:
    match_id = state.get("match_id")
    if match_id:
        return str(match_id)

    batting = (state.get("batting_team") or "unknown").lower().replace(" ", "-")
    bowling = (state.get("bowling_team") or "unknown").lower().replace(" ", "-")
    return f"{batting}_vs_{bowling}"


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _last_entry_for_match(rows: List[Dict[str, Any]], match_key: str) -> Optional[Dict[str, Any]]:
    for row in reversed(rows):
        if row.get("match_key") == match_key:
            return row
    return None


def _opening_from_shift(previous_wp: Any, current_wp: Any, wickets_delta: int, runs_delta: int) -> str:
    if previous_wp is not None and current_wp is not None:
        wp_delta = current_wp - previous_wp
        if wp_delta <= -5:
            return f"Win probability dropped from {previous_wp}% to {current_wp}%"
        if wp_delta >= 5:
            return f"Win probability improved from {previous_wp}% to {current_wp}%"
        return f"Win probability stayed fairly steady at {current_wp}%"

    if wickets_delta > 0 or runs_delta <= 4:
        return "Pressure increased over the last over"
    if runs_delta >= 10:
        return "Momentum improved over the last over"
    return "The last over stayed relatively balanced"


def _pressure_reasons(runs_delta: int, wickets_delta: int, overs_delta: float) -> List[str]:
    if wickets_delta > 0 and runs_delta <= 4:
        return ["there was a wicket and dot-ball pressure in a low-scoring over"]

    reasons: List[str] = []
    if wickets_delta > 0:
        wicket_word = "wicket" if wickets_delta == 1 else "wickets"
        reasons.append(f"{wickets_delta} {wicket_word} fell")

    if overs_delta < 0.5:
        return reasons
    if runs_delta <= 4:
        reasons.append("dot-ball pressure built up in a low-scoring over")
    elif runs_delta >= 12:
        reasons.append("boundary pressure was released with a big over")
    elif runs_delta >= 8:
        reasons.append("the batting side kept the over productive")

    return reasons


def _rrr_reason(previous_rrr: Any, current_rrr: Any) -> Optional[str]:
    if previous_rrr is None or current_rrr is None:
        return None

    rrr_delta = round(current_rrr - previous_rrr, 2)
    if rrr_delta >= 0.5:
        return f"the required rate climbed from {previous_rrr} to {current_rrr}"
    if rrr_delta <= -0.5:
        return f"the required rate eased from {previous_rrr} to {current_rrr}"
    return None


def build_over_change_reason(previous_entry: Optional[Dict[str, Any]], current_entry: Dict[str, Any]) -> str:
    if previous_entry is None:
        return "Baseline snapshot saved. Over-by-over movement will be explained from the next completed over."

    runs_delta = (current_entry.get("runs") or 0) - (previous_entry.get("runs") or 0)
    wickets_delta = (current_entry.get("wickets") or 0) - (previous_entry.get("wickets") or 0)
    overs_delta = _safe_float(current_entry.get("overs")) - _safe_float(previous_entry.get("overs"))

    opening = _opening_from_shift(
        previous_entry.get("win_probability"),
        current_entry.get("win_probability"),
        wickets_delta,
        runs_delta,
    )

    reasons = _pressure_reasons(runs_delta, wickets_delta, overs_delta)
    rate_reason = _rrr_reason(previous_entry.get("required_run_rate"), current_entry.get("required_run_rate"))
    if rate_reason:
        reasons.append(rate_reason)
    if not reasons:
        reasons.append("the scoreboard barely moved")

    return f"{opening} because {' and '.join(reasons)}."


def build_snapshot_signature(state: Optional[Dict[str, Any]]) -> tuple:
    if state is None:
        return ()
    return tuple(state.get(field) for field in TRACKED_FIELDS)


def has_score_changed(previous_state: Optional[Dict[str, Any]], current_state: Dict[str, Any]) -> bool:
    return build_snapshot_signature(previous_state) != build_snapshot_signature(current_state)


def build_history_entry(
    state: Dict[str, Any],
    enriched_state: Dict[str, Any],
    plan: Dict[str, str],
    agent_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    evaluation = (agent_context or {}).get("evaluation", {})
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "match_key": get_match_key(state),
        "match_id": state.get("match_id"),
        "batting_team": state.get("batting_team"),
        "bowling_team": state.get("bowling_team"),
        "runs": state.get("runs"),
        "wickets": state.get("wickets"),
        "score": f"{state.get('runs', 0)}/{state.get('wickets', 0)}",
        "overs": state.get("overs"),
        OVER_BUCKET_FIELD: int(_safe_float(state.get("overs"))),
        "phase": enriched_state.get("phase"),
        "total_overs": enriched_state.get("total_overs"),
        "match_context": enriched_state.get("match_context"),
        "current_run_rate": enriched_state.get("current_run_rate"),
        "required_run_rate": enriched_state.get("required_run_rate"),
        "win_probability": enriched_state.get("estimated_win_probability"),
        "strategy": plan.get("strategy"),
        "target_runs": plan.get("target_runs"),
        "risk_level": plan.get("risk_level"),
        "focus": plan.get("focus"),
        "bowling_strategy": plan.get("bowling_strategy"),
        "bowling_risk_level": plan.get("bowling_risk_level"),
        "bowling_focus": plan.get("bowling_focus"),
        "agent_objective": (agent_context or {}).get("objective"),
        "agent_confidence": (agent_context or {}).get("confidence"),
        "agent_evaluation_status": evaluation.get("status"),
        "agent_evaluation_headline": evaluation.get("headline"),
        "agent_batting_evaluation_status": evaluation.get("batting_status"),
        "agent_batting_evaluation_headline": evaluation.get("batting_headline"),
        "agent_bowling_evaluation_status": evaluation.get("bowling_status"),
        "agent_bowling_evaluation_headline": evaluation.get("bowling_headline"),
        "source": state.get("source", "local"),
        "source_url": state.get("source_url"),
    }


def _read_history_rows(history_path: Path) -> List[Dict[str, Any]]:
    if not history_path.exists():
        return []

    rows: List[Dict[str, Any]] = []
    with history_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def save_history_entry(entry: Dict[str, Any], history_path: Path | str = DEFAULT_HISTORY_PATH) -> bool:
    history_path = Path(history_path)
    history_path.parent.mkdir(parents=True, exist_ok=True)

    existing_rows = _read_history_rows(history_path)
    previous_entry = _last_entry_for_match(existing_rows, entry.get("match_key", ""))

    if previous_entry and previous_entry.get(OVER_BUCKET_FIELD) == entry.get(OVER_BUCKET_FIELD):
        return False

    previous_wp = previous_entry.get("win_probability") if previous_entry else None
    current_wp = entry.get("win_probability")
    entry["previous_win_probability"] = previous_wp
    entry["win_probability_delta"] = (
        None if previous_wp is None or current_wp is None else current_wp - previous_wp
    )
    entry["change_reason"] = build_over_change_reason(previous_entry, entry)

    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return True


def load_history(match_key: Optional[str] = None, limit: int = 50, history_path: Path | str = DEFAULT_HISTORY_PATH) -> List[Dict[str, Any]]:
    history_path = Path(history_path)
    rows = _read_history_rows(history_path)

    if match_key:
        rows = [row for row in rows if row.get("match_key") == match_key]

    return rows[-limit:]
