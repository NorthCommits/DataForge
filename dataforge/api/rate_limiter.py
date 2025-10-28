from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Deque, Optional


class TokenBucketRateLimiter:
    """Simple async token bucket supporting requests-per-minute and burst control."""

    def __init__(self, rate_per_minute: int, burst: Optional[int] = None) -> None:
        self.rate_per_minute = max(1, rate_per_minute)
        self.capacity = burst if burst is not None else self.rate_per_minute
        self.tokens = float(self.capacity)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        rate_per_sec = self.rate_per_minute / 60.0
        self.tokens = min(self.capacity, self.tokens + elapsed * rate_per_sec)
        self.last_refill = now

    async def acquire(self, tokens: float = 1.0) -> None:
        async with self._lock:
            while True:
                self._refill()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return
                needed = tokens - self.tokens
                rate_per_sec = self.rate_per_minute / 60.0
                await asyncio.sleep(needed / rate_per_sec)
