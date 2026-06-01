"""Self Model — Tracks agent capabilities, weaknesses, load, and recent outcomes."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import deque
from typing import Optional
import uuid


@dataclass
class Outcome:
    id: str = field(default_factory=lambda: f"OUTCOME-{uuid.uuid4().hex[:8]}")
    task_id: str = ""
    success: bool = False
    notes: str = ""
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Capability:
    name: str = ""
    proficiency: float = 0.5  # 0..1
    description: str = ""


@dataclass
class Weakness:
    name: str = ""
    severity: float = 0.5  # 0..1
    notes: str = ""


class SelfModel:
    """Agent's self-representation: what it can do, what it can't, how it's doing."""

    LOAD_THRESHOLDS = {"idle": 0, "light": 3, "moderate": 7, "heavy": 12, "overloaded": 9999}

    def __init__(
        self,
        identity_facts: Optional[dict] = None,
        capabilities: Optional[list[Capability]] = None,
        weaknesses: Optional[list[Weakness]] = None,
        outcomes_capacity: int = 100,
    ):
        self.identity_facts: dict = dict(identity_facts or {})
        self.capabilities: list[Capability] = list(capabilities or [])
        self.known_weaknesses: list[Weakness] = list(weaknesses or [])
        self.recent_outcomes: deque[Outcome] = deque(maxlen=outcomes_capacity)
        self.current_load: int = 0
        self._failure_streak: int = 0
        self._success_streak: int = 0

    # ---------- capability + weakness management ----------

    def add_capability(self, name: str, proficiency: float = 0.5, description: str = "") -> Capability:
        cap = Capability(name=name, proficiency=max(0.0, min(1.0, proficiency)), description=description)
        self.capabilities.append(cap)
        return cap

    def add_weakness(self, name: str, severity: float = 0.5, notes: str = "") -> Weakness:
        w = Weakness(name=name, severity=max(0.0, min(1.0, severity)), notes=notes)
        self.known_weaknesses.append(w)
        return w

    def has_capability(self, name: str) -> bool:
        return any(c.name == name for c in self.capabilities)

    # ---------- load ----------

    def set_load(self, load: int) -> None:
        self.current_load = max(0, int(load))

    def increment_load(self, delta: int = 1) -> int:
        self.current_load = max(0, self.current_load + int(delta))
        return self.current_load

    def load_status(self) -> str:
        for label in ("idle", "light", "moderate", "heavy", "overloaded"):
            if self.current_load <= self.LOAD_THRESHOLDS[label]:
                return label
        return "overloaded"

    # ---------- outcomes ----------

    def record_outcome(self, task_id: str, success: bool, notes: str = "") -> Outcome:
        outcome = Outcome(task_id=task_id, success=bool(success), notes=notes)
        self.recent_outcomes.append(outcome)
        if success:
            self._success_streak += 1
            self._failure_streak = 0
        else:
            self._failure_streak += 1
            self._success_streak = 0
        return outcome

    def success_rate(self, last_n: Optional[int] = None) -> float:
        outcomes = list(self.recent_outcomes)
        if last_n is not None:
            outcomes = outcomes[-int(last_n):]
        if not outcomes:
            return 0.0
        successes = sum(1 for o in outcomes if o.success)
        return successes / len(outcomes)

    def failure_streak(self) -> int:
        return self._failure_streak

    def success_streak(self) -> int:
        return self._success_streak

    def top_weakness(self) -> Optional[Weakness]:
        if not self.known_weaknesses:
            return None
        return max(self.known_weaknesses, key=lambda w: w.severity)

    def top_capability(self) -> Optional[Capability]:
        if not self.capabilities:
            return None
        return max(self.capabilities, key=lambda c: c.proficiency)

    def self_assessment(self) -> dict:
        top_w = self.top_weakness()
        top_c = self.top_capability()
        sr = self.success_rate()
        sr_recent = self.success_rate(last_n=10)
        # Confidence heuristic.
        confidence = 0.3 + 0.7 * sr_recent
        if self._failure_streak >= 3:
            confidence *= 0.6
        confidence = max(0.0, min(1.0, confidence))
        return {
            "identity": dict(self.identity_facts),
            "capability_count": len(self.capabilities),
            "weakness_count": len(self.known_weaknesses),
            "top_capability": (
                {"name": top_c.name, "proficiency": round(top_c.proficiency, 3)}
                if top_c else None
            ),
            "top_weakness": (
                {"name": top_w.name, "severity": round(top_w.severity, 3)}
                if top_w else None
            ),
            "success_rate": round(sr, 4),
            "recent_success_rate": round(sr_recent, 4),
            "success_streak": self._success_streak,
            "failure_streak": self._failure_streak,
            "outcome_count": len(self.recent_outcomes),
            "current_load": self.current_load,
            "load_status": self.load_status(),
            "estimated_confidence": round(confidence, 4),
            "assessed_at": datetime.now(timezone.utc).isoformat(),
        }

    def snapshot(self) -> dict:
        return {
            "identity_facts": dict(self.identity_facts),
            "capabilities": [
                {"name": c.name, "proficiency": c.proficiency, "description": c.description}
                for c in self.capabilities
            ],
            "known_weaknesses": [
                {"name": w.name, "severity": w.severity, "notes": w.notes}
                for w in self.known_weaknesses
            ],
            "current_load": self.current_load,
            "recent_outcomes": [
                {"task_id": o.task_id, "success": o.success, "ts": o.ts, "notes": o.notes}
                for o in self.recent_outcomes
            ],
            "taken_at": datetime.now(timezone.utc).isoformat(),
        }
