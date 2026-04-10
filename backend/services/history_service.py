from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.core.history_store import load_history, save_history_entry
from backend.services.storage_service import fetch_history_records, persist_history_record


def fetch_history(match_key: Optional[str] = None, limit: int = 50, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    db_rows = fetch_history_records(match_key=match_key, limit=limit, user_id=user_id)
    if db_rows:
        return db_rows
    return load_history(match_key=match_key, limit=limit)


def persist_entry(entry: Dict[str, Any], user_id: Optional[int] = None) -> bool:
    json_saved = save_history_entry(entry)
    db_saved = persist_history_record(entry, user_id=user_id)
    return bool(json_saved or db_saved)
