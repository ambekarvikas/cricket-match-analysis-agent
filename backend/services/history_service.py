from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.core.history_store import load_history, save_history_entry


def fetch_history(match_key: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    return load_history(match_key=match_key, limit=limit)


def persist_entry(entry: Dict[str, Any]) -> bool:
    return save_history_entry(entry)
