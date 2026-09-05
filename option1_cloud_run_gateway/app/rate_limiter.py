"""In-Memory High-Performance Rate Limiter & DoS Shield.

Provides sliding-window rate limiting per client IP to protect cryptographic,
ZKP verification, and DAG compilation routes from resource exhaustion.
"""

import time
import threading
from typing import Dict, List, Optional, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class SlidingWindowRateLimiter:
    """Thread-safe sliding window rate limiter with auto-eviction."""

    def __init__(
        self,
        default_limit: int = 600,
        crypto_limit: int = 150,
        window_seconds: int = 60,
        max_tracked_ips: int = 20_000,
    ):
        self.default_limit = default_limit
        self.crypto_limit = crypto_limit
        self.window_seconds = window_seconds
        self.max_tracked_ips = max_tracked_ips
        self._buckets: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from Forwarded / X-Forwarded-For or client host."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"

    def _cleanup_old_entries(self, now: float):
        """Purge entries older than the sliding window."""
        cutoff = now - self.window_seconds
        expired_ips = []
        for ip, timestamps in self._buckets.items():
            valid_ts = [t for t in timestamps if t > cutoff]
            if not valid_ts:
                expired_ips.append(ip)
            else:
                self._buckets[ip] = valid_ts

        for ip in expired_ips:
            self._buckets.pop(ip, None)

        if len(self._buckets) > self.max_tracked_ips:
            sorted_ips = sorted(self._buckets.items(), key=lambda x: x[1][-1] if x[1] else 0)
            excess = len(self._buckets) - self.max_tracked_ips
            for ip, _ in sorted_ips[:excess]:
                self._buckets.pop(ip, None)

    def check_rate_limit(self, request: Request) -> Tuple[bool, int, int, int]:
        """Check if request exceeds rate limit.

        Returns (is_allowed, remaining, limit, retry_after).
        """
        path = request.url.path

        # Whitelist health checks, discovery metadata, and static assets
        if (
            path in ("/healthz", "/health", "/api/health/all", "/")
            or path.startswith("/.well-known")
            or path.endswith(".ico")
            or path.endswith(".png")
            or path.endswith(".jpg")
            or path.endswith(".css")
            or path.endswith(".js")
        ):
            return True, 9999, 9999, 0

        # Determine limit for path (stricter for compute-heavy crypto / zkp)
        is_crypto = any(
            frag in path
            for frag in (
                "/verify",
                "/zkp",
                "/action",
                "/sign",
                "/compile-dag",
                "/benchmarks/run",
            )
        )
        limit = self.crypto_limit if is_crypto else self.default_limit

        ip = self._get_client_ip(request)
        bucket_key = f"{ip}:{'crypto' if is_crypto else 'general'}"
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            if now - self._last_cleanup > 30.0:
                self._cleanup_old_entries(now)
                self._last_cleanup = now

            timestamps = self._buckets.setdefault(bucket_key, [])
            valid_ts = [t for t in timestamps if t > cutoff]
            self._buckets[bucket_key] = valid_ts

            if len(valid_ts) >= limit:
                earliest = valid_ts[0]
                retry_after = max(1, int(earliest + self.window_seconds - now))
                return False, 0, limit, retry_after

            valid_ts.append(now)
            remaining = limit - len(valid_ts)
            return True, remaining, limit, 0

    def is_allowed(self, client_id: str, path: str = "/") -> Tuple[bool, int]:
        """Convenience method checking rate limit for a client identifier and path.

        Returns (is_allowed, retry_after).
        """
        is_crypto = any(
            frag in path
            for frag in (
                "/verify",
                "/zkp",
                "/action",
                "/sign",
                "/compile-dag",
                "/benchmarks/run",
            )
        )
        limit = self.crypto_limit if is_crypto else self.default_limit
        bucket_key = f"{client_id}:{'crypto' if is_crypto else 'general'}"
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            if now - self._last_cleanup > 30.0:
                self._cleanup_old_entries(now)
                self._last_cleanup = now

            timestamps = self._buckets.setdefault(bucket_key, [])
            valid_ts = [t for t in timestamps if t > cutoff]
            self._buckets[bucket_key] = valid_ts

            if len(valid_ts) >= limit:
                earliest = valid_ts[0]
                retry_after = max(1, int(earliest + self.window_seconds - now))
                return False, retry_after

            valid_ts.append(now)
            return True, 0

    def reset(self):
        """Clear all rate limit buckets (useful for test automation)."""
        with self._lock:
            self._buckets.clear()


GLOBAL_RATE_LIMITER = SlidingWindowRateLimiter()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """FastAPI / Starlette middleware enforcing in-memory sliding window rate limits."""

    def __init__(
        self,
        app,
        limiter: Optional[SlidingWindowRateLimiter] = None,
        default_limit: Optional[int] = None,
        crypto_limit: Optional[int] = None,
        window_seconds: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(app)
        if limiter is not None:
            self.limiter = limiter
        elif default_limit is not None or crypto_limit is not None or window_seconds is not None:
            self.limiter = SlidingWindowRateLimiter(
                default_limit=default_limit or 600,
                crypto_limit=crypto_limit or 150,
                window_seconds=window_seconds or 60,
            )
        else:
            self.limiter = GLOBAL_RATE_LIMITER

    async def dispatch(self, request: Request, call_next):
        allowed, remaining, limit, retry_after = self.limiter.check_rate_limit(request)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": f"Rate limit exceeded ({limit} req/{self.limiter.window_seconds}s). Please retry in {retry_after}s.",
                    "retryAfter": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                },
            )

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        return response
