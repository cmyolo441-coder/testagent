"""Experiment Reproducer — manage reproduction attempts for a claimed result."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class ReproductionAttempt:
    id: str = field(default_factory=lambda: f"REP-{uuid.uuid4().hex[:8]}")
    experiment_id: str = ""
    reproduced_by: str = "system"
    outcome: str = "pending"      # "pending"|"reproduced"|"failed"|"partial"
    deviation: float = 0.0        # |result - claim| / |claim|
    notes: str = ""
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: Optional[str] = None
    artifacts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {**self.__dict__}


class ExperimentReproducer:
    def __init__(self):
        self.attempts: dict[str, ReproductionAttempt] = {}

    def submit(self, experiment_id: str, reproduced_by: str = "system") -> ReproductionAttempt:
        a = ReproductionAttempt(experiment_id=experiment_id, reproduced_by=reproduced_by)
        self.attempts[a.id] = a
        return a

    def finalize(self, attempt_id: str, outcome: str, deviation: float = 0.0,
                 notes: str = "", artifacts: list[str] | None = None) -> bool:
        a = self.attempts.get(attempt_id)
        if not a: return False
        a.outcome = outcome
        a.deviation = deviation
        a.notes = notes
        a.artifacts = artifacts or []
        a.finished_at = datetime.now(timezone.utc).isoformat()
        return True

    def reproduction_rate(self, experiment_id: str) -> dict:
        atts = [a for a in self.attempts.values() if a.experiment_id == experiment_id]
        total = len(atts)
        reproduced = sum(1 for a in atts if a.outcome == "reproduced")
        partial = sum(1 for a in atts if a.outcome == "partial")
        return {
            "experiment_id": experiment_id,
            "attempts": total,
            "reproduced": reproduced,
            "partial": partial,
            "rate": (reproduced + 0.5 * partial) / total if total else 0.0,
            "verified": (reproduced + partial) >= 2,
        }
