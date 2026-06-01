"""SelfModel — capabilities, weaknesses, recent outcomes, load, identity"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
from collections import deque
import uuid


@dataclass
class Capability:
    name: str
    proficiency: float = 0.5  # 0..1
    last_used: Optional[str] = None
    usage_count: int = 0
    tags: list[str] = field(default_factory=list)

    def touch(self) -> None:
        self.last_used = datetime.now(timezone.utc).isoformat()
        self.usage_count += 1
        self.proficiency = min(1.0, self.proficiency + 0.005)


@dataclass
class Weakness:
    name: str
    severity: float = 0.5  # 0..1
    description: str = ""
    workaround: Optional[str] = None


@dataclass
class Outcome:
    outcome_id: str
    success: bool
    task: str
    notes: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.outcome_id:
            self.outcome_id = f"OUT-{uuid.uuid4().hex[:8]}"


class SelfModel:
    """Track agent capabilities, weaknesses, recent outcomes, load, and identity."""

    def __init__(
        self,
        agent_name: str = "astra",
        identity: Optional[dict] = None,
        outcome_window: int = 50,
        max_load: float = 1.0,
    ):
        self.agent_name = agent_name
        self.identity: dict = dict(identity or {})
        self.identity.setdefault("name", agent_name)
        self.identity.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        self.identity.setdefault("model_id", f"SELF-{uuid.uuid4().hex[:8]}")
        self.capabilities: dict[str, Capability] = {}
        self.weaknesses: dict[str, Weakness] = {}
        self.outcomes: deque[Outcome] = deque(maxlen=max(1, outcome_window))
        self.current_load: float = 0.0
        self.max_load: float = max(0.01, float(max_load))

    # ---- Capabilities ----
    def add_capability(
        self,
        name: str,
        proficiency: float = 0.5,
        tags: Optional[list[str]] = None,
    ) -> Capability:
        cap = Capability(
            name=name,
            proficiency=max(0.0, min(1.0, float(proficiency))),
            tags=list(tags or []),
        )
        self.capabilities[name] = cap
        return cap

    def update_capability(self, name: str, delta_proficiency: float) -> Optional[Capability]:
        cap = self.capabilities.get(name)
        if cap is None:
            return None
        cap.proficiency = max(0.0, min(1.0, cap.proficiency + float(delta_proficiency)))
        return cap

    def use_capability(self, name: str) -> Optional[Capability]:
        cap = self.capabilities.get(name)
        if cap is None:
            return None
        cap.touch()
        return cap

    def has_capability(self, name: str, min_proficiency: float = 0.0) -> bool:
        cap = self.capabilities.get(name)
        return cap is not None and cap.proficiency >= min_proficiency

    # ---- Weaknesses ----
    def add_weakness(
        self,
        name: str,
        severity: float = 0.5,
        description: str = "",
        workaround: Optional[str] = None,
    ) -> Weakness:
        w = Weakness(
            name=name,
            severity=max(0.0, min(1.0, float(severity))),
            description=description,
            workaround=workaround,
        )
        self.weaknesses[name] = w
        return w

    # ---- Outcomes ----
    def record_outcome(self, success: bool, task: str, notes: str = "") -> Outcome:
        out = Outcome(outcome_id="", success=success, task=task, notes=notes)
        self.outcomes.append(out)
        return out

    def success_rate(self, last_n: Optional[int] = None) -> float:
        items = list(self.outcomes)
        if last_n is not None:
            items = items[-last_n:]
        if not items:
            return 0.0
        return round(sum(1 for o in items if o.success) / len(items), 6)

    # ---- Load ----
    def set_load(self, load: float) -> None:
        self.current_load = max(0.0, float(load))

    def add_load(self, delta: float) -> None:
        self.current_load = max(0.0, self.current_load + float(delta))

    def load_ratio(self) -> float:
        return round(min(1.0, self.current_load / self.max_load), 6)

    # ---- Reflection ----
    def self_assessment(self) -> dict:
        sr_recent = self.success_rate(last_n=10)
        sr_all = self.success_rate()
        strong = sorted(
            (c for c in self.capabilities.values() if c.proficiency >= 0.7),
            key=lambda c: c.proficiency,
            reverse=True,
        )
        weak_caps = sorted(
            (c for c in self.capabilities.values() if c.proficiency < 0.4),
            key=lambda c: c.proficiency,
        )
        top_weaknesses = sorted(self.weaknesses.values(), key=lambda w: w.severity, reverse=True)[:5]
        load_ratio = self.load_ratio()
        status = "healthy"
        if load_ratio > 0.9 or sr_recent < 0.4:
            status = "degraded"
        elif load_ratio > 0.7 or sr_recent < 0.6:
            status = "stressed"
        recommendations = []
        if load_ratio > 0.85:
            recommendations.append("shed load or defer non-critical tasks")
        if sr_recent < 0.5 and len(self.outcomes) >= 5:
            recommendations.append("trigger reflection on recent failures")
        for w in top_weaknesses[:2]:
            if w.workaround:
                recommendations.append(f"use workaround for {w.name}: {w.workaround}")
        if not recommendations:
            recommendations.append("operate normally")
        return {
            "agent_name": self.agent_name,
            "identity": dict(self.identity),
            "status": status,
            "load_ratio": load_ratio,
            "current_load": round(self.current_load, 6),
            "max_load": self.max_load,
            "success_rate_recent_10": sr_recent,
            "success_rate_all": sr_all,
            "outcomes_recorded": len(self.outcomes),
            "capabilities_total": len(self.capabilities),
            "strong_capabilities": [c.name for c in strong[:5]],
            "weak_capabilities": [c.name for c in weak_caps[:5]],
            "top_weaknesses": [
                {"name": w.name, "severity": w.severity, "workaround": w.workaround}
                for w in top_weaknesses
            ],
            "recommendations": recommendations,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def snapshot(self) -> dict:
        return {
            "snapshot_id": f"SSNAP-{uuid.uuid4().hex[:8]}",
            "agent_name": self.agent_name,
            "identity": dict(self.identity),
            "capabilities": {
                k: {
                    "name": c.name,
                    "proficiency": c.proficiency,
                    "last_used": c.last_used,
                    "usage_count": c.usage_count,
                    "tags": list(c.tags),
                }
                for k, c in self.capabilities.items()
            },
            "weaknesses": {
                k: {
                    "name": w.name,
                    "severity": w.severity,
                    "description": w.description,
                    "workaround": w.workaround,
                }
                for k, w in self.weaknesses.items()
            },
            "outcomes": [
                {
                    "outcome_id": o.outcome_id,
                    "success": o.success,
                    "task": o.task,
                    "notes": o.notes,
                    "timestamp": o.timestamp,
                }
                for o in self.outcomes
            ],
            "current_load": self.current_load,
            "max_load": self.max_load,
        }
