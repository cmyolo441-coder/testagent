"""Civilization Health Monitor — Roll-up health metrics across runtime."""
from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class HealthReport:
    active_agents: int = 0
    total_agents: int = 0
    avg_reputation: float = 0.0
    dispute_rate: float = 0.0
    productivity_score: float = 0.0
    decision_count: int = 0
    anomaly_flags: list[str] = field(default_factory=list)
    ts: float = field(default_factory=time.time)


class CivilizationHealthMonitor:
    """Aggregate signals from society, reputation, and decision log."""

    def __init__(self, society=None, reputation=None, decision_log=None,
                 labor_allocator=None,
                 low_reputation_threshold: float = 0.3,
                 high_dispute_threshold: float = 0.4):
        self.society = society
        self.reputation = reputation
        self.decision_log = decision_log
        self.labor_allocator = labor_allocator
        self.low_reputation_threshold = low_reputation_threshold
        self.high_dispute_threshold = high_dispute_threshold
        self.history: list[HealthReport] = []

    def _agent_counts(self) -> tuple[int, int]:
        if self.society is None or not getattr(self.society, "members", None):
            return 0, 0
        members = list(self.society.members.values())
        active = sum(1 for m in members if getattr(m, "active", True))
        return active, len(members)

    def _avg_reputation(self) -> float:
        if self.reputation is not None and getattr(self.reputation, "scores", None):
            vals = list(self.reputation.scores.values())
            if vals:
                return sum(vals) / len(vals)
        if self.society is not None and getattr(self.society, "members", None):
            members = list(self.society.members.values())
            if members:
                return sum(getattr(m, "reputation", 0.5) for m in members) / len(members)
        return 0.0

    def _dispute_rate(self) -> float:
        if self.society is None or not getattr(self.society, "interactions", None):
            return 0.0
        interactions = self.society.interactions
        if not interactions:
            return 0.0
        disputes = sum(1 for i in interactions
                       if i.get("type") == "dispute" or i.get("outcome") == "conflict")
        return disputes / len(interactions)

    def _productivity_score(self) -> float:
        # Mix: completed tasks per active agent + decision throughput.
        active, _ = self._agent_counts()
        active = max(active, 1)
        completed = 0
        if self.society is not None and getattr(self.society, "members", None):
            completed = sum(getattr(m, "tasks_completed", 0) for m in self.society.members.values())
        if self.labor_allocator is not None and getattr(self.labor_allocator, "tasks", None):
            completed += sum(1 for t in self.labor_allocator.tasks.values() if t.status == "done")
        decisions = len(self.decision_log.entries) if self.decision_log is not None else 0
        raw = (completed / active) * 0.7 + (decisions / max(active, 1)) * 0.3
        return max(0.0, min(1.0, raw / 10.0))

    def _decision_count(self) -> int:
        if self.decision_log is None:
            return 0
        return len(getattr(self.decision_log, "entries", []))

    def compute_report(self) -> HealthReport:
        active, total = self._agent_counts()
        avg_rep = self._avg_reputation()
        dispute = self._dispute_rate()
        productivity = self._productivity_score()
        decisions = self._decision_count()

        flags: list[str] = []
        if total > 0 and active / max(total, 1) < 0.5:
            flags.append("low_activity")
        if avg_rep < self.low_reputation_threshold:
            flags.append("low_reputation")
        if dispute > self.high_dispute_threshold:
            flags.append("high_dispute_rate")
        if productivity < 0.1 and total > 0:
            flags.append("low_productivity")
        if total == 0:
            flags.append("no_population")

        report = HealthReport(
            active_agents=active,
            total_agents=total,
            avg_reputation=avg_rep,
            dispute_rate=dispute,
            productivity_score=productivity,
            decision_count=decisions,
            anomaly_flags=flags,
        )
        self.history.append(report)
        return report

    def latest(self) -> Optional[HealthReport]:
        return self.history[-1] if self.history else None
