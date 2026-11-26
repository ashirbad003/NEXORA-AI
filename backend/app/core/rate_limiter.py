import time
import asyncio
from typing import Dict, Tuple, Optional
from collections import deque
from fastapi import Request, HTTPException, status

class SlidingWindowRateLimiter:
    """
    In-memory, thread-safe sliding window rate limiter.
    Limits requests based on client IP or user ID over a rolling window.
    """
    def __init__(self, default_limit: int = 60, default_window_seconds: int = 60):
        self.default_limit = default_limit
        self.default_window_seconds = default_window_seconds
        # key -> deque of timestamps
        self._windows: Dict[str, deque] = {}
        self._lock = asyncio.Lock()

    async def is_allowed(
        self,
        key: str,
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None
    ) -> Tuple[bool, int, int]:
        """
        Check if request under key is allowed.
        Returns: (is_allowed, remaining_quota, retry_after_seconds)
        """
        max_requests = limit or self.default_limit
        window = window_seconds or self.default_window_seconds
        now = time.time()
        cutoff = now - window

        async with self._lock:
            # Memory safety: if dictionary exceeds 10,000 keys, prune empty keys
            if len(self._windows) > 10000:
                empty_keys = [k for k, v in self._windows.items() if not v or v[-1] <= cutoff]
                for k in empty_keys[:1000]:
                    del self._windows[k]

            if key not in self._windows:
                self._windows[key] = deque()

            q = self._windows[key]
            # Prune timestamps older than window cutoff
            while q and q[0] <= cutoff:
                q.popleft()

            if len(q) < max_requests:
                q.append(now)
                remaining = max_requests - len(q)
                return True, remaining, 0
            else:
                retry_after = int(q[0] + window - now) + 1
                return False, 0, max(1, retry_after)

    async def check_rate_limit(
        self,
        request: Request,
        key_prefix: str = "global",
        limit: int = 60,
        window_seconds: int = 60
    ):
        """
        FastAPI dependency helper to enforce rate limit.
        Uses request.client.host directly to prevent spoofed X-Forwarded-For headers
        from bypassing IP-based rate limiting unless behind a verified trusted proxy.
        """
        client_ip = request.client.host if request.client else "unknown_client"
        rate_key = f"{key_prefix}:{client_ip}"
        
        allowed, remaining, retry_after = await self.is_allowed(
            rate_key, limit=limit, window_seconds=window_seconds
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Please retry after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )

# Global rate limiter instance
rate_limiter = SlidingWindowRateLimiter()
