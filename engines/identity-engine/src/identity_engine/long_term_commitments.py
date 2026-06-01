"""Long-Term Commitments — Persistent promises the agent makes about itself."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class LongTermCommitment:
    id: str = field(default_factory=lambda: f"LTC-{uuid.uuid4().hex[:10]}")
    statement: str = ""
    made_at: str = field(default_factory=_now_iso)
    expires_at: Optional[str] = None
    witnesses: list[str] = field(default_factory=list)
    status: str = "active"  # active, fulfilled, broken
    updated_at: str = field(default_factory=_now_iso)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "statement": self.statement,
            "made_at": self.made_at,
            "expires_at": self.expires_at,
            "witnesses": list(self.witnesses),
            "status": self.status,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }


class CommitmentLedger:
    """In-memory append-mostly store of long-term commitments."""

    VALID_STATUSES = {"active", "fulfilled", "broken"}

    def __init__(self):
        self.commitments: dict[str, LongTermCommitment] = {}

    def add(self, statement: str, witnesses: Optional[list[str]] = None,
            expires_at: Optional[str] = None,
            metadata: Optional[dict] = None) -> LongTermCommitment:
        c = LongTermCommitment(
            statement=statement,
            witnesses=list(witnesses or []),
            expires_at=expires_at,
            metadata=dict(metadata or {}),
        )
        self.commitments[c.id] = c
        return c

    def get(self, commitment_id: str) -> Optional[LongTermCommitment]:
        return self.commitments.get(commitment_id)

    def list_active(self) -> list[LongTermCommitment]:
        now = datetime.now(timezone.utc).isoformat()
        out = []
        for c in self.commitments.values():
            if c.status != "active":
                continue
            if c.expires_at and c.expires_at < now:
                continue
            out.append(c)
        return out

    def _set_status(self, commitment_id: str, status: str) -> Optional[LongTermCommitment]:
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        c = self.commitments.get(commitment_id)
        if not c:
            return None
        c.status = status
        c.updated_at = _now_iso()
        return c

    def mark_fulfilled(self, commitment_id: str) -> Optional[LongTermCommitment]:
        return self._set_status(commitment_id, "fulfilled")

    def mark_broken(self, commitment_id: str) -> Optional[LongTermCommitment]:
        return self._set_status(commitment_id, "broken")

    def stats(self) -> dict:
        active = sum(1 for c in self.commitments.values() if c.status == "active")
        fulfilled = sum(1 for c in self.commitments.values() if c.status == "fulfilled")
        broken = sum(1 for c in self.commitments.values() if c.status == "broken")
        return {
            "total": len(self.commitments),
            "active": active,
            "fulfilled": fulfilled,
            "broken": broken,
        }

    def to_dict(self) -> dict:
        return {"commitments": [c.to_dict() for c in self.commitments.values()]}
