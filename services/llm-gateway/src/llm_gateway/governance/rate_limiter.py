"""Rate Limiter — Token-bucket rate limiting per key."""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class _Bucket:
    rate_per_minute: float
    burst: int
    tokens: float
    last_refill: float
    accepted: int = 0
    rejected: int = 0


class RateLimiter:
    """Classic token-bucket limiter with per-key configuration.

    Refills continuously using ``time.monotonic()``. Unconfigured keys inherit
    the default rate/burst supplied at construction time.
    """

    def __init__(self, default_rate_per_minute: float = 60.0, default_burst: int = 60):
        self.default_rate_per_minute = float(default_rate_per_minute)
        self.default_burst = int(default_burst)
        self._buckets: dict[str, _Bucket] = {}

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    def configure(self, key: str, rate_per_minute: float, burst: int) -> None:
        if rate_per_minute < 0 or burst < 0:
            raise ValueError("rate_per_minute and burst must be non-negative")
        now = time.monotonic()
        existing = self._buckets.get(key)
        if existing is None:
            self._buckets[key] = _Bucket(
                rate_per_minute=float(rate_per_minute),
                burst=int(burst),
                tokens=float(burst),
                last_refill=now,
            )
        else:
            self._refill(existing, now)
            existing.rate_per_minute = float(rate_per_minute)
            existing.burst = int(burst)
            existing.tokens = min(existing.tokens, float(burst))

    # ------------------------------------------------------------------
    # Acquire
    # ------------------------------------------------------------------
    def try_acquire(self, key: str, n: int = 1) -> bool:
        if n <= 0:
            return True
        bucket = self._get_or_create(key)
        now = time.monotonic()
        self._refill(bucket, now)
        if bucket.tokens >= n:
            bucket.tokens -= n
            bucket.accepted += n
            return True
        bucket.rejected += n
        return False

    # ------------------------------------------------------------------
    # Inspection / control
    # ------------------------------------------------------------------
    def remaining(self, key: str) -> int:
        bucket = self._get_or_create(key)
        self._refill(bucket, time.monotonic())
        return int(bucket.tokens)

    def reset(self, key: str) -> None:
        bucket = self._buckets.get(key)
        if bucket is None:
            return
        bucket.tokens = float(bucket.burst)
        bucket.last_refill = time.monotonic()
        bucket.accepted = 0
        bucket.rejected = 0

    def stats(self) -> dict:
        out: dict[str, dict] = {}
        now = time.monotonic()
        for key, bucket in self._buckets.items():
            self._refill(bucket, now)
            out[key] = {
                "rate_per_minute": bucket.rate_per_minute,
                "burst": bucket.burst,
                "tokens": round(bucket.tokens, 4),
                "accepted": bucket.accepted,
                "rejected": bucket.rejected,
            }
        return out

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _get_or_create(self, key: str) -> _Bucket:
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = _Bucket(
                rate_per_minute=self.default_rate_per_minute,
                burst=self.default_burst,
                tokens=float(self.default_burst),
                last_refill=time.monotonic(),
            )
            self._buckets[key] = bucket
        return bucket

    @staticmethod
    def _refill(bucket: _Bucket, now: float) -> None:
        elapsed = max(0.0, now - bucket.last_refill)
        if elapsed <= 0.0:
            return
        per_second = bucket.rate_per_minute / 60.0
        bucket.tokens = min(float(bucket.burst), bucket.tokens + elapsed * per_second)
        bucket.last_refill = now
