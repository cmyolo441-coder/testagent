"""Decision Memory — Track decisions, rationale, and outcomes"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class Decision:
    id: str = field(default_factory=lambda: f"DEC-{uuid.uuid4().hex[:12]}")
    title: str = ""
    description: str = ""
    decision_type: str = ""  # architectural, tactical, strategic, operational, emergency
    context: str = ""
    options_considered: list[dict] = field(default_factory=list)
    chosen_option: str = ""
    rationale: str = ""
    confidence: float = 0.7
    risk_level: str = "medium"  # low, medium, high, critical
    outcome: str = ""  # pending, success, failure, partial
    outcome_notes: str = ""
    reversible: bool = True
    made_by: str = ""  # agent_id or user_id
    approved_by: Optional[str] = None
    mission_id: Optional[str] = None
    task_id: Optional[str] = None
    related_decisions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    outcome_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "decision_type": self.decision_type,
            "chosen_option": self.chosen_option,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "outcome": self.outcome,
            "reversible": self.reversible,
            "tags": self.tags,
            "created_at": self.created_at,
        }


class DecisionMemory:
    """Tracks decisions, their rationale, and outcomes."""

    def __init__(self, store=None):
        self.store = store
        self.decisions: dict[str, Decision] = {}
        self._type_index: dict[str, list[str]] = {}
        self._mission_index: dict[str, list[str]] = {}

    def store_decision(self, title: str, description: str = "",
                       decision_type: str = "operational", context: str = "",
                       options_considered: list[dict] = None, chosen_option: str = "",
                       rationale: str = "", confidence: float = 0.7,
                       risk_level: str = "medium", reversible: bool = True,
                       made_by: str = "", approved_by: str = None,
                       mission_id: str = None, task_id: str = None,
                       tags: list[str] = None) -> Decision:
        decision = Decision(
            title=title,
            description=description,
            decision_type=decision_type,
            context=context,
            options_considered=options_considered or [],
            chosen_option=chosen_option,
            rationale=rationale,
            confidence=confidence,
            risk_level=risk_level,
            reversible=reversible,
            made_by=made_by,
            approved_by=approved_by,
            mission_id=mission_id,
            task_id=task_id,
            tags=tags or [],
        )
        self.decisions[decision.id] = decision

        if decision_type not in self._type_index:
            self._type_index[decision_type] = []
        self._type_index[decision_type].append(decision.id)

        if mission_id:
            if mission_id not in self._mission_index:
                self._mission_index[mission_id] = []
            self._mission_index[mission_id].append(decision.id)

        if self.store:
            from memory_engine.stores.sqlite_store import MemoryRecord
            record = MemoryRecord(
                memory_type="decision",
                content=f"Decision: {title} ({decision_type})",
                context={"decision_type": decision_type, "risk_level": risk_level},
                importance=0.8 if risk_level in ("high", "critical") else 0.5,
                tags=tags or [],
                mission_id=mission_id,
                task_id=task_id,
                metadata={"decision_id": decision.id},
            )
            self.store.store(record)

        return decision

    def get_decision_history(self, decision_type: str = None,
                             mission_id: str = None, limit: int = 50) -> list[Decision]:
        results = list(self.decisions.values())
        if decision_type:
            results = [d for d in results if d.decision_type == decision_type]
        if mission_id:
            results = [d for d in results if d.mission_id == mission_id]
        results.sort(key=lambda d: d.created_at, reverse=True)
        return results[:limit]

    def get_decision(self, decision_id: str) -> Optional[Decision]:
        return self.decisions.get(decision_id)

    def record_outcome(self, decision_id: str, outcome: str,
                       outcome_notes: str = "") -> bool:
        decision = self.decisions.get(decision_id)
        if not decision:
            return False
        decision.outcome = outcome
        decision.outcome_notes = outcome_notes
        decision.outcome_at = datetime.now(timezone.utc).isoformat()
        decision.updated_at = decision.outcome_at
        return True

    def get_successful_decisions(self, min_confidence: float = 0.5) -> list[Decision]:
        return [
            d for d in self.decisions.values()
            if d.outcome == "success" and d.confidence >= min_confidence
        ]

    def get_failed_decisions(self) -> list[Decision]:
        return [d for d in self.decisions.values() if d.outcome == "failure"]

    def get_pending_decisions(self) -> list[Decision]:
        return [d for d in self.decisions.values() if d.outcome == ""]

    def get_high_risk(self) -> list[Decision]:
        return [
            d for d in self.decisions.values()
            if d.risk_level in ("high", "critical")
        ]

    def get_learning_points(self) -> list[dict]:
        learnings = []
        for d in self.decisions.values():
            if d.outcome in ("failure", "partial"):
                learnings.append({
                    "decision_id": d.id,
                    "title": d.title,
                    "rationale": d.rationale,
                    "outcome": d.outcome,
                    "lesson": f"Decision '{d.title}' resulted in {d.outcome}: {d.outcome_notes}",
                })
        return learnings

    def get_stats(self) -> dict:
        decisions = list(self.decisions.values())
        by_type = {}
        by_outcome = {}
        for d in decisions:
            by_type[d.decision_type] = by_type.get(d.decision_type, 0) + 1
            if d.outcome:
                by_outcome[d.outcome] = by_outcome.get(d.outcome, 0) + 1
        return {
            "total_decisions": len(decisions),
            "by_type": by_type,
            "by_outcome": by_outcome,
            "pending_count": len(self.get_pending_decisions()),
        }
