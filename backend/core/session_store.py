from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

DEFAULT_SESSION_PATH = Path(__file__).resolve().parent.parent / "data" / "session_history.jsonl"


def make_session_id(match_key: str, provided: Optional[str] = None) -> str:
    if provided and str(provided).strip():
        return str(provided).strip()

    safe_key = (match_key or "match-session").replace(" ", "-").replace("/", "-")
    return f"{safe_key}-{uuid4().hex[:8]}"


def _read_session_rows(session_path: Path | str = DEFAULT_SESSION_PATH) -> List[Dict[str, Any]]:
    session_path = Path(session_path)
    if not session_path.exists():
        return []

    rows: List[Dict[str, Any]] = []
    with session_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def save_session_entry(entry: Dict[str, Any], session_path: Path | str = DEFAULT_SESSION_PATH) -> None:
    session_path = Path(session_path)
    session_path.parent.mkdir(parents=True, exist_ok=True)
    with session_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_session_entries(session_id: str, limit: int = 30, session_path: Path | str = DEFAULT_SESSION_PATH) -> List[Dict[str, Any]]:
    rows = _read_session_rows(session_path)
    filtered = [row for row in rows if row.get("session_id") == session_id]
    return filtered[-limit:]


def build_session_entry(
    session_id: str,
    match_key: str,
    state: Dict[str, Any],
    plan: Dict[str, Any],
    what_if: List[Dict[str, Any]],
    confidence: int,
    action_summary: str,
    cache_status: str,
) -> Dict[str, Any]:
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "session_id": session_id,
        "match_key": match_key,
        "score": f"{state.get('runs', 0)}/{state.get('wickets', 0)}",
        "runs": state.get("runs"),
        "wickets": state.get("wickets"),
        "overs": state.get("overs"),
        "phase": state.get("phase"),
        "win_probability": state.get("estimated_win_probability"),
        "bowling_win_probability": state.get("estimated_bowling_win_probability"),
        "recommended_action": plan.get("recommended_action"),
        "bowling_recommended_action": plan.get("bowling_recommended_action"),
        "decision_window": plan.get("decision_window"),
        "priority": plan.get("priority"),
        "confidence": confidence,
        "cache_status": cache_status,
        "action_summary": action_summary,
        "what_if": what_if,
    }


def _best_scenario(entries: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    scenarios: List[Dict[str, Any]] = []
    for entry in entries:
        scenarios.extend(entry.get("what_if") or [])

    if not scenarios:
        return None

    return max(scenarios, key=lambda scenario: int(scenario.get("win_probability_delta") or 0))


def build_session_summary(session_id: str, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not entries:
        return {
            "session_id": session_id,
            "snapshot_count": 0,
            "trend_summary": "No saved session context yet.",
            "latest_score": None,
            "momentum_delta": 0,
            "best_scenario": None,
        }

    first = entries[0]
    latest = entries[-1]
    first_wp = int(first.get("win_probability") or 50)
    latest_wp = int(latest.get("win_probability") or 50)
    momentum_delta = latest_wp - first_wp

    if momentum_delta >= 10:
        trend_summary = f"Momentum has improved strongly across the session, moving from {first_wp}% to {latest_wp}%."
    elif momentum_delta >= 4:
        trend_summary = f"Momentum has improved gradually across the session, rising from {first_wp}% to {latest_wp}%."
    elif momentum_delta <= -10:
        trend_summary = f"Momentum has slipped sharply across the session, falling from {first_wp}% to {latest_wp}%."
    elif momentum_delta <= -4:
        trend_summary = f"Momentum has drifted against the batting side, sliding from {first_wp}% to {latest_wp}%."
    else:
        trend_summary = f"The session has stayed relatively balanced, with win probability moving from {first_wp}% to {latest_wp}%."

    return {
        "session_id": session_id,
        "match_key": latest.get("match_key"),
        "snapshot_count": len(entries),
        "latest_score": latest.get("score"),
        "latest_phase": latest.get("phase"),
        "momentum_delta": momentum_delta,
        "trend_summary": trend_summary,
        "latest_recommendation": latest.get("recommended_action"),
        "decision_window": latest.get("decision_window"),
        "best_scenario": _best_scenario(entries),
        "last_updated": latest.get("timestamp"),
    }
