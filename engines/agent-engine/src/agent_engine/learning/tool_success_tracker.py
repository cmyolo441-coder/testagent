"""Tool Success Tracker — Per-tool reliability metrics."""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
from collections import deque


@dataclass
class ToolStats:
    tool: str = ""
    calls: int = 0
    successes: int = 0
    failures: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    last_error: Optional[str] = None
    last_used: Optional[str] = None
    recent_failures: deque = field(default_factory=lambda: deque(maxlen=50))


class ToolSuccessTracker:
    """Tracks success/failure counts and latency per tool."""

    def __init__(self):
        self.stats: dict[str, ToolStats] = {}

    def _ensure(self, tool: str) -> ToolStats:
        if tool not in self.stats:
            self.stats[tool] = ToolStats(tool=tool)
        return self.stats[tool]

    def record(
        self,
        tool: str,
        success: bool,
        latency_ms: float = 0.0,
        error: Optional[str] = None,
    ) -> ToolStats:
        s = self._ensure(tool)
        s.calls += 1
        s.total_latency_ms += float(latency_ms)
        s.avg_latency_ms = s.total_latency_ms / s.calls if s.calls else 0.0
        s.last_used = datetime.now(timezone.utc).isoformat()
        if success:
            s.successes += 1
        else:
            s.failures += 1
            s.last_error = error
            s.recent_failures.append({
                "ts": s.last_used,
                "error": error or "unknown",
                "latency_ms": float(latency_ms),
            })
        return s

    def success_rate(self, tool: str) -> float:
        s = self.stats.get(tool)
        if not s or s.calls == 0:
            return 0.0
        return s.successes / s.calls

    def top_n(self, n: int = 5, min_calls: int = 1) -> list[tuple[str, float]]:
        """Return top N tools ordered by reliability (success_rate)."""
        ranked = [
            (tool, self.success_rate(tool))
            for tool, s in self.stats.items()
            if s.calls >= min_calls
        ]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[: max(0, int(n))]

    def recent_failures(self, tool: str, n: int = 10) -> list[dict]:
        s = self.stats.get(tool)
        if not s:
            return []
        items = list(s.recent_failures)
        return items[-int(n):] if n > 0 else items

    def to_dict(self) -> dict:
        return {
            tool: {
                "calls": s.calls,
                "successes": s.successes,
                "failures": s.failures,
                "success_rate": self.success_rate(tool),
                "avg_latency_ms": s.avg_latency_ms,
                "last_error": s.last_error,
                "last_used": s.last_used,
            }
            for tool, s in self.stats.items()
        }
