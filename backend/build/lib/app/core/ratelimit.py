"""Lightweight in-memory rate limiting for sensitive endpoints.

Per-process fixed window keyed by client IP + scope. Fine for a single-instance
deployment (Cloud Run with low concurrency); a multi-instance production setup
should swap this for a shared store (e.g. Redis).
"""

import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Request

from app.core.config import settings
from app.core.errors import AppError

_hits: dict[str, deque[float]] = defaultdict(deque)


def reset_rate_limits() -> None:
    _hits.clear()


def rate_limit(max_requests: int, window_seconds: int, scope: str) -> Callable[[Request], None]:
    """Return a FastAPI dependency enforcing `max_requests` per `window_seconds`."""

    def dependency(request: Request) -> None:
        if not settings.rate_limit_enabled:
            return
        ip = request.client.host if request.client else "unknown"
        key = f"{scope}:{ip}"
        now = time.monotonic()
        bucket = _hits[key]
        cutoff = now - window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= max_requests:
            raise AppError(
                429,
                "RATE_LIMITED",
                "Too many requests. Please slow down and try again shortly.",
                {"retry_after_seconds": window_seconds},
            )
        bucket.append(now)

    return dependency
