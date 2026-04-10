from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional

from backend.services.data_service import list_live_matches

logger = logging.getLogger("cricket_agent.live_refresh")
LIVE_REFRESH_INTERVAL_SECONDS = int(os.getenv("LIVE_REFRESH_INTERVAL_SECONDS", "30"))
LIVE_CACHE_TTL_SECONDS = int(os.getenv("LIVE_CACHE_TTL_SECONDS", "45"))


class LiveMatchRefreshService:
    """Background refresher for live match listings so scraping is not repeated on every request."""

    def __init__(self) -> None:
        self.refresh_interval = max(10, LIVE_REFRESH_INTERVAL_SECONDS)
        self.cache_ttl = max(self.refresh_interval, LIVE_CACHE_TTL_SECONDS)
        self._snapshot: Dict[str, Any] = {
            "items": [],
            "timestamp": 0.0,
            "last_error": None,
            "refresh_count": 0,
        }
        self._lock = asyncio.Lock()
        self._task: Optional[asyncio.Task[None]] = None

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        await self.refresh_once()
        self._task = asyncio.create_task(self._refresh_loop())
        logger.info("Live refresh service started | interval=%s", self.refresh_interval)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None
            logger.info("Live refresh service stopped")

    async def _refresh_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self.refresh_interval)
                await self.refresh_once()
        except asyncio.CancelledError:
            logger.info("Live refresh loop cancelled")
            raise

    async def refresh_once(self) -> List[Dict[str, Any]]:
        try:
            items = await asyncio.to_thread(list_live_matches)
            async with self._lock:
                self._snapshot = {
                    "items": items,
                    "timestamp": time.time(),
                    "last_error": None,
                    "refresh_count": int(self._snapshot.get("refresh_count") or 0) + 1,
                }
            return items
        except Exception as exc:
            logger.warning("Live refresh failed | error=%s", exc)
            async with self._lock:
                self._snapshot["last_error"] = str(exc)
            return list(self._snapshot.get("items") or [])

    async def get_matches(self, series_hint: Optional[str] = None) -> List[Dict[str, Any]]:
        async with self._lock:
            snapshot = dict(self._snapshot)

        age = time.time() - float(snapshot.get("timestamp") or 0)
        items = list(snapshot.get("items") or [])
        filtered = self._apply_series_hint(items, series_hint)

        if filtered and age <= self.cache_ttl:
            return filtered
        if items and not series_hint and age <= self.cache_ttl:
            return items

        refreshed = await self.refresh_once()
        return self._apply_series_hint(refreshed, series_hint)

    def status(self) -> Dict[str, Any]:
        timestamp = float(self._snapshot.get("timestamp") or 0)
        age = round(max(0.0, time.time() - timestamp), 2) if timestamp else None
        return {
            "refresh_interval_seconds": self.refresh_interval,
            "cache_ttl_seconds": self.cache_ttl,
            "last_refresh_age_seconds": age,
            "cached_matches": len(self._snapshot.get("items") or []),
            "last_error": self._snapshot.get("last_error"),
            "refresh_count": self._snapshot.get("refresh_count") or 0,
        }

    @staticmethod
    def _apply_series_hint(items: List[Dict[str, Any]], series_hint: Optional[str]) -> List[Dict[str, Any]]:
        if not series_hint:
            return items
        needle = series_hint.strip().lower()
        if not needle:
            return items
        filtered: List[Dict[str, Any]] = []
        for item in items:
            haystack = " ".join(
                str(item.get(key, "")) for key in ("series", "title", "status", "match_id")
            ).lower()
            if needle in haystack:
                filtered.append(item)
        return filtered


live_refresh_service = LiveMatchRefreshService()
