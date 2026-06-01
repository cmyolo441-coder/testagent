"""Promise Memory — Track commitments, promises, and their fulfillment"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class Promise:
    id: str = field(default_factory=lambda: f"PRM-{uuid.uuid4().hex[:12]}")
    description: str = ""
    promise_type: str = ""  # task, deadline, deliverable, behavior, policy
    status: str = "pending"  # pending, in_progress, fulfilled, broken, deferred
    made_to: str = ""  # user_id or agent_id
    made_by: str = ""  # agent_id or user_id
    mission_id: Optional[str] = None
    task_id: Optional[str] = None
    deadline: Optional[str] = None
    priority: str = "medium"  # low, medium, high, critical
    confidence: float = 0.8  # how confident we are in fulfilling this
    context: dict = field(default_factory=dict)
    fulfillment_evidence: list[str] = field(default_factory=list)
    broken_reason: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    fulfilled_at: Optional[str] = None

    @property
    def is_overdue(self) -> bool:
        if not self.deadline or self.status in ("fulfilled", "broken"):
            return False
        return datetime.now(timezone.utc).isoformat() > self.deadline

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "promise_type": self.promise_type,
            "status": self.status,
            "made_to": self.made_to,
            "deadline": self.deadline,
            "priority": self.priority,
            "is_overdue": self.is_overdue,
            "tags": self.tags,
            "created_at": self.created_at,
        }


class PromiseMemory:
    """Tracks commitments and promise fulfillment."""

    def __init__(self, store=None):
        self.store = store
        self.promises: dict[str, Promise] = {}
        self._user_promises: dict[str, list[str]] = {}
        self._mission_promises: dict[str, list[str]] = {}

    def store_promise(self, description: str, promise_type: str = "task",
                      made_to: str = "", made_by: str = "", mission_id: str = None,
                      task_id: str = None, deadline: str = None,
                      priority: str = "medium", confidence: float = 0.8,
                      tags: list[str] = None, context: dict = None) -> Promise:
        promise = Promise(
            description=description,
            promise_type=promise_type,
            made_to=made_to,
            made_by=made_by,
            mission_id=mission_id,
            task_id=task_id,
            deadline=deadline,
            priority=priority,
            confidence=confidence,
            tags=tags or [],
            context=context or {},
        )
        self.promises[promise.id] = promise

        if made_to:
            if made_to not in self._user_promises:
                self._user_promises[made_to] = []
            self._user_promises[made_to].append(promise.id)

        if mission_id:
            if mission_id not in self._mission_promises:
                self._mission_promises[mission_id] = []
            self._mission_promises[mission_id].append(promise.id)

        if self.store:
            from memory_engine.stores.sqlite_store import MemoryRecord
            record = MemoryRecord(
                memory_type="promise",
                content=f"Promise: {description} ({promise_type}/{priority})",
                context={"made_to": made_to, "deadline": deadline},
                importance=0.9 if priority == "critical" else 0.6,
                tags=tags or [],
                mission_id=mission_id,
                task_id=task_id,
                metadata={"promise_id": promise.id},
            )
            self.store.store(record)

        return promise

    def check_fulfilled(self, promise_id: str) -> dict:
        promise = self.promises.get(promise_id)
        if not promise:
            return {"error": "Promise not found", "fulfilled": False}
        return {
            "promise_id": promise.id,
            "description": promise.description,
            "status": promise.status,
            "fulfilled": promise.status == "fulfilled",
            "is_overdue": promise.is_overdue,
            "deadline": promise.deadline,
            "evidence": promise.fulfillment_evidence,
        }

    def fulfill(self, promise_id: str, evidence: str = "") -> bool:
        promise = self.promises.get(promise_id)
        if not promise or promise.status in ("fulfilled", "broken"):
            return False
        promise.status = "fulfilled"
        promise.fulfilled_at = datetime.now(timezone.utc).isoformat()
        promise.updated_at = promise.fulfilled_at
        if evidence:
            promise.fulfillment_evidence.append(evidence)
        return True

    def break_promise(self, promise_id: str, reason: str = "") -> bool:
        promise = self.promises.get(promise_id)
        if not promise or promise.status in ("fulfilled", "broken"):
            return False
        promise.status = "broken"
        promise.broken_reason = reason
        promise.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def get_pending(self, user_id: str = None) -> list[Promise]:
        results = [p for p in self.promises.values() if p.status in ("pending", "in_progress")]
        if user_id:
            results = [p for p in results if p.made_to == user_id]
        return results

    def get_overdue(self) -> list[Promise]:
        return [p for p in self.promises.values() if p.is_overdue]

    def get_by_user(self, user_id: str) -> list[Promise]:
        promise_ids = self._user_promises.get(user_id, [])
        return [self.promises[pid] for pid in promise_ids if pid in self.promises]

    def get_by_mission(self, mission_id: str) -> list[Promise]:
        promise_ids = self._mission_promises.get(mission_id, [])
        return [self.promises[pid] for pid in promise_ids if pid in self.promises]

    def get_fulfillment_rate(self, user_id: str = None) -> float:
        promises = list(self.promises.values())
        if user_id:
            promises = [p for p in promises if p.made_to == user_id]
        if not promises:
            return 1.0
        fulfilled = sum(1 for p in promises if p.status == "fulfilled")
        return fulfilled / len(promises)

    def get_stats(self) -> dict:
        promises = list(self.promises.values())
        by_status = {}
        for p in promises:
            by_status[p.status] = by_status.get(p.status, 0) + 1
        return {
            "total_promises": len(promises),
            "by_status": by_status,
            "overdue_count": len(self.get_overdue()),
            "fulfillment_rate": self.get_fulfillment_rate(),
        }
