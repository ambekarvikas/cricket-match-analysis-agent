from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select

from backend.db.database import get_db_session
from backend.db.models import AnalysisHistoryRecord, SessionSnapshotRecord

logger = logging.getLogger("cricket_agent.storage_service")


def _safe_load(payload_json: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    try:
        loaded = json.loads(payload_json)
        return loaded if isinstance(loaded, dict) else fallback
    except (TypeError, json.JSONDecodeError):
        return fallback


def persist_history_record(entry: Dict[str, Any], user_id: Optional[int] = None) -> bool:
    try:
        with get_db_session() as db:
            db.add(
                AnalysisHistoryRecord(
                    user_id=user_id,
                    match_key=str(entry.get("match_key") or "unknown-match"),
                    batting_team=entry.get("batting_team"),
                    bowling_team=entry.get("bowling_team"),
                    score=entry.get("score"),
                    overs=entry.get("overs"),
                    phase=entry.get("phase"),
                    win_probability=entry.get("win_probability"),
                    strategy=entry.get("strategy"),
                    payload_json=json.dumps(entry, ensure_ascii=False),
                )
            )
        return True
    except Exception as exc:
        logger.warning("DB history persistence failed | match_key=%s | error=%s", entry.get("match_key"), exc)
        return False


def fetch_history_records(match_key: Optional[str] = None, limit: int = 50, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    try:
        with get_db_session() as db:
            stmt = select(AnalysisHistoryRecord).order_by(desc(AnalysisHistoryRecord.created_at)).limit(limit)
            if match_key:
                stmt = stmt.where(AnalysisHistoryRecord.match_key == match_key)
            if user_id is not None:
                stmt = stmt.where(AnalysisHistoryRecord.user_id == user_id)
            records = list(db.scalars(stmt).all())
        rows = [
            _safe_load(
                record.payload_json,
                {
                    "match_key": record.match_key,
                    "score": record.score,
                    "overs": record.overs,
                    "phase": record.phase,
                    "win_probability": record.win_probability,
                    "strategy": record.strategy,
                },
            )
            for record in reversed(records)
        ]
        return rows
    except Exception as exc:
        logger.warning("DB history fetch failed | match_key=%s | error=%s", match_key, exc)
        return []


def persist_session_record(entry: Dict[str, Any], user_id: Optional[int] = None) -> bool:
    try:
        with get_db_session() as db:
            db.add(
                SessionSnapshotRecord(
                    user_id=user_id,
                    session_id=str(entry.get("session_id") or "anonymous-session"),
                    match_key=str(entry.get("match_key") or "unknown-match"),
                    score=entry.get("score"),
                    overs=entry.get("overs"),
                    phase=entry.get("phase"),
                    win_probability=entry.get("win_probability"),
                    recommended_action=entry.get("recommended_action"),
                    payload_json=json.dumps(entry, ensure_ascii=False),
                )
            )
        return True
    except Exception as exc:
        logger.warning("DB session persistence failed | session_id=%s | error=%s", entry.get("session_id"), exc)
        return False


def fetch_session_records(session_id: str, limit: int = 30, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    try:
        with get_db_session() as db:
            stmt = (
                select(SessionSnapshotRecord)
                .where(SessionSnapshotRecord.session_id == session_id)
                .order_by(desc(SessionSnapshotRecord.created_at))
                .limit(limit)
            )
            if user_id is not None:
                stmt = stmt.where(SessionSnapshotRecord.user_id == user_id)
            records = list(db.scalars(stmt).all())
        rows = [
            _safe_load(
                record.payload_json,
                {
                    "session_id": record.session_id,
                    "match_key": record.match_key,
                    "score": record.score,
                    "overs": record.overs,
                    "phase": record.phase,
                    "win_probability": record.win_probability,
                    "recommended_action": record.recommended_action,
                },
            )
            for record in reversed(records)
        ]
        return rows
    except Exception as exc:
        logger.warning("DB session fetch failed | session_id=%s | error=%s", session_id, exc)
        return []
