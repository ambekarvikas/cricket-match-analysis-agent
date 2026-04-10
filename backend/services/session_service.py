from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.core.session_store import (
    build_session_entry,
    build_session_summary,
    load_session_entries,
    make_session_id,
    save_session_entry,
)


def resolve_session_id(match_key: str, session_id: Optional[str] = None) -> str:
    return make_session_id(match_key, session_id)


def persist_session_snapshot(
    session_id: str,
    match_key: str,
    state: Dict[str, Any],
    plan: Dict[str, Any],
    what_if: List[Dict[str, Any]],
    confidence: int,
    action_summary: str,
    cache_status: str,
) -> Dict[str, Any]:
    entry = build_session_entry(
        session_id=session_id,
        match_key=match_key,
        state=state,
        plan=plan,
        what_if=what_if,
        confidence=confidence,
        action_summary=action_summary,
        cache_status=cache_status,
    )
    save_session_entry(entry)
    return entry


def fetch_session(session_id: str, limit: int = 30) -> Dict[str, Any]:
    entries = load_session_entries(session_id=session_id, limit=limit)
    summary = build_session_summary(session_id=session_id, entries=entries)
    return {
        "session_id": session_id,
        "summary": summary,
        "entries": entries,
    }
