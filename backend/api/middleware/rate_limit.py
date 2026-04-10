from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "90"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
_SKIP_PREFIXES = ("/health", "/docs", "/redoc", "/openapi.json")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory request throttling for local and single-instance deployments."""

    def __init__(
        self,
        app,
        requests_per_window: int = RATE_LIMIT_REQUESTS,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
    ) -> None:
        super().__init__(app)
        self.requests_per_window = max(0, int(requests_per_window))
        self.window_seconds = max(1, int(window_seconds))
        self._requests: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _should_skip(self, path: str) -> bool:
        return path.startswith(_SKIP_PREFIXES) or self.requests_per_window == 0

    def _client_key(self, request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next):
        if self._should_skip(request.url.path):
            return await call_next(request)

        client_key = self._client_key(request)
        now = time.time()
        retry_after = 0

        with self._lock:
            bucket = self._requests[client_key]
            cutoff = now - self.window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= self.requests_per_window:
                retry_after = max(1, int(self.window_seconds - (now - bucket[0])))
            else:
                bucket.append(now)

            remaining = max(0, self.requests_per_window - len(bucket))

        if retry_after:
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please retry shortly.",
                    "retry_after_seconds": retry_after,
                    "limit": self.requests_per_window,
                    "window_seconds": self.window_seconds,
                },
            )
            response.headers["Retry-After"] = str(retry_after)
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_window)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Window"] = str(self.window_seconds)
            return response

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_window)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(self.window_seconds)
        return response
