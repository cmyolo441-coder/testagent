"""Memory Decay Policy — Apply importance-based decay to memories"""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional


@dataclass
class DecayConfig:
    half_life_days: float = 30.0
    min_importance: float = 0.05
    access_boost: float = 0.1
    max_boost_per_access: float = 0.5
    pin_threshold: float = 0.9
    critical_floor: float = 0.3


@dataclass
class DecayResult:
    memory_id: str
    original_importance: float
    decayed_importance: float
    was_forgotten: bool
    was_pinned: bool
    access_count: int
    age_days: float


class MemoryDecayPolicy:
    """Applies time-based and access-based decay to memories."""

    def __init__(self, config: DecayConfig = None):
        self.config = config or DecayConfig()

    def apply(self, memories: list[dict]) -> list[DecayResult]:
        results = []
        now = datetime.now(timezone.utc)

        for mem in memories:
            mem_id = mem.get("id", "")
            importance = mem.get("importance", 0.5)
            created_at = mem.get("created_at", now.isoformat())
            last_accessed = mem.get("last_accessed") or created_at
            access_count = mem.get("access_count", 0)

            try:
                created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                age_days = (now - created_dt).total_seconds() / 86400.0
            except (ValueError, TypeError):
                age_days = 0.0

            try:
                last_access_dt = datetime.fromisoformat(last_accessed.replace("Z", "+00:00"))
                days_since_access = (now - last_access_dt).total_seconds() / 86400.0
            except (ValueError, TypeError):
                days_since_access = age_days

            decayed = self._calculate_decay(importance, age_days, days_since_access, access_count)

            was_pinned = importance >= self.config.pin_threshold
            was_forgotten = decayed <= self.config.min_importance and not was_pinned

            if was_forgotten:
                decayed = 0.0

            results.append(DecayResult(
                memory_id=mem_id,
                original_importance=importance,
                decayed_importance=round(decayed, 4),
                was_forgotten=was_forgotten,
                was_pinned=was_pinned,
                access_count=access_count,
                age_days=round(age_days, 2),
            ))

        return results

    def _calculate_decay(self, importance: float, age_days: float,
                         days_since_access: float, access_count: int) -> float:
        if importance >= self.config.pin_threshold:
            return importance

        half_life = self.config.half_life_days
        time_factor = 0.5 ** (age_days / half_life)
        base = importance * time_factor

        access_boost = min(
            self.config.access_boost * (access_count ** 0.5),
            self.config.max_boost_per_access,
        )

        recency_factor = 0.5 ** (days_since_access / (half_life * 2))
        recency_boost = recency_factor * 0.1

        return max(self.config.min_importance, min(1.0, base + access_boost + recency_boost))

    def get_decay_curve(self, importance: float, days: int = 365,
                        step: int = 7) -> list[dict]:
        curve = []
        for day in range(0, days + 1, step):
            decayed = self._calculate_decay(importance, day, day, 0)
            curve.append({"day": day, "importance": round(decayed, 4)})
        return curve

    def get_retention_probability(self, importance: float, age_days: float) -> float:
        if importance >= self.config.pin_threshold:
            return 1.0
        half_life = self.config.half_life_days
        return 0.5 ** (age_days / half_life)

    def suggest_pin(self, memories: list[dict], max_pins: int = 20) -> list[str]:
        candidates = [
            (m.get("id", ""), m.get("importance", 0), m.get("access_count", 0))
            for m in memories
        ]
        candidates.sort(key=lambda x: (x[1] * 0.7 + min(x[2], 10) * 0.3), reverse=True)
        return [cid for cid, _, _ in candidates[:max_pins]]
