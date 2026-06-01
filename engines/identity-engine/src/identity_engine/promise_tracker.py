"""Promise Tracker — Short-horizon obligations to specific recipients."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Promise:
    id: str = field(default_factory=lambda: f"PROMISE-{uuid.uuid4().hex[:10]}")
    content: str = ""
    made_to: str = ""  # user_id or agent_id
    due_at: Optional[str] = None  # ISO timestamp
    status: str = "open"  # open, done, missed
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    snoozed_count: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "made_to": self.made_to,
            "due_at": self.due_at,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "snoozed_count": self.snoozed_count,
            "metadata": dict(self.metadata),
        }


class PromiseTracker:
    """Track open / done / missed promises and surface overdue ones."""

    VALID_STATUSES = {"open", "done", "missed"}

    def __init__(self):
        self.promises: dict[str, Promise] = {}

    def create_promise(self, content: str, made_to: str,
                       due_at: Optional[str] = None,
                       metadata: Optional[dict] = None) -> Promise:
        p = Promise(
            content=content,
            made_to=made_to,
            due_at=due_at,
            metadata=dict(metadata or {}),
        )
        self.promises[p.id] = p
        return p

    def get(self, promise_id: str) -> Optional[Promise]:
        return self.promises.get(promise_id)

    def fulfill(self, promise_id: str) -> Optional[Promise]:
        p = self.promises.get(promise_id)
        if not p:
            return None
        p.status = "done"
        p.updated_at = _now_iso()
        return p

    def miss(self, promise_id: str) -> Optional[Promise]:
        p = self.promises.get(promise_id)
        if not p:
            return None
        p.status = "missed"
        p.updated_at = _now_iso()
        return p

    def snooze(self, promise_id: str, additional_seconds: int = 3600) -> Optional[Promise]:
        p = self.promises.get(promise_id)
        if not p:
            return None
        base = datetime.now(timezone.utc)
        if p.due_at:
            try:
                cur = datetime.fromisoformat(p.due_at)
                if cur > base:
                    base = cur
            except ValueError:
                pass
        new_due = base + timedelta(seconds=additional_seconds)
        p.due_at = new_due.isoformat()
        p.snoozed_count += 1
        p.updated_at = _now_iso()
        return p

    def get_overdue(self, now: Optional[str] = None) -> list[Promise]:
        now_iso = now or _now_iso()
        out: list[Promise] = []
        for p in self.promises.values():
            if p.status != "open":
                continue
            if p.due_at and p.due_at < now_iso:
                out.append(p)
        return out

    def get_open(self, made_to: Optional[str] = None) -> list[Promise]:
        return [
            p for p in self.promises.values()
            if p.status == "open" and (made_to is None or p.made_to == made_to)
        ]

    def stats(self) -> dict:
        by_status: dict[str, int] = {s: 0 for s in self.VALID_STATUSES}
        for p in self.promises.values():
            by_status[p.status] = by_status.get(p.status, 0) + 1
        return {
            "total": len(self.promises),
            "by_status": by_status,
            "overdue": len(self.get_overdue()),
        }
