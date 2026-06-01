"""Reputation System — Per-agent reputation scores with decay and history."""
from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class ReputationEvent:
    agent_id: str
    delta: float
    reason: str
    old_score: float
    new_score: float
    ts: float = field(default_factory=time.time)


class ReputationSystem:
    """Track and adjust per-agent reputation in [0, 1]."""

    DEFAULT_SCORE = 0.5

    def __init__(self, default_score: float = DEFAULT_SCORE):
        self.default_score = default_score
        self.scores: dict[str, float] = {}
        self.history: list[ReputationEvent] = []

    def get(self, agent_id: str) -> float:
        return self.scores.get(agent_id, self.default_score)

    def adjust(self, agent_id: str, delta: float, reason: str = "") -> float:
        old = self.get(agent_id)
        new = max(0.0, min(1.0, old + delta))
        self.scores[agent_id] = new
        self.history.append(ReputationEvent(
            agent_id=agent_id,
            delta=delta,
            reason=reason,
            old_score=old,
            new_score=new,
        ))
        return new

    def decay(self, rate: float = 0.01) -> None:
        """Pull every score toward the default by `rate` (0..1)."""
        rate = max(0.0, min(1.0, rate))
        for agent_id, score in list(self.scores.items()):
            self.scores[agent_id] = score + (self.default_score - score) * rate

    def top_n(self, n: int = 5) -> list[tuple[str, float]]:
        return sorted(self.scores.items(), key=lambda kv: kv[1], reverse=True)[:n]

    def bottom_n(self, n: int = 5) -> list[tuple[str, float]]:
        return sorted(self.scores.items(), key=lambda kv: kv[1])[:n]

    def history_for(self, agent_id: str) -> list[ReputationEvent]:
        return [e for e in self.history if e.agent_id == agent_id]

    def stats(self) -> dict:
        if not self.scores:
            return {"tracked": 0, "avg": self.default_score, "events": len(self.history)}
        vals = list(self.scores.values())
        return {
            "tracked": len(vals),
            "avg": sum(vals) / len(vals),
            "min": min(vals),
            "max": max(vals),
            "events": len(self.history),
        }
