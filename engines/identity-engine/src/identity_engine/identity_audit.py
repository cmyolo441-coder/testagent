"""Identity Audit — Append-only, hash-chained audit log of identity events."""
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_hash(payload: Any) -> str:
    """Stable hash of an arbitrary JSON-serializable payload."""
    try:
        encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    except (TypeError, ValueError):
        encoded = repr(payload).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass
class AuditEvent:
    event_id: str = field(default_factory=lambda: f"AUD-{uuid.uuid4().hex[:12]}")
    action: str = ""  # create_manifest, update_values, mark_fulfilled, ...
    before_hash: str = ""
    after_hash: str = ""
    actor: str = "system"
    ts: str = field(default_factory=_now_iso)
    prev_event_id: Optional[str] = None
    chain_hash: str = ""  # hash of (prev_chain_hash + event fields)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "action": self.action,
            "before_hash": self.before_hash,
            "after_hash": self.after_hash,
            "actor": self.actor,
            "ts": self.ts,
            "prev_event_id": self.prev_event_id,
            "chain_hash": self.chain_hash,
            "metadata": dict(self.metadata),
        }

    def _fields_for_chain(self) -> dict:
        return {
            "event_id": self.event_id,
            "action": self.action,
            "before_hash": self.before_hash,
            "after_hash": self.after_hash,
            "actor": self.actor,
            "ts": self.ts,
            "prev_event_id": self.prev_event_id,
            "metadata": self.metadata,
        }


class IdentityAudit:
    """Append-only ledger with a verifiable hash chain."""

    GENESIS = "0" * 64

    def __init__(self):
        self.events: list[AuditEvent] = []

    @staticmethod
    def hash_state(state: Any) -> str:
        return _canonical_hash(state)

    def append(self, action: str, before_state: Any, after_state: Any,
               actor: str = "system",
               metadata: Optional[dict] = None) -> AuditEvent:
        before_hash = _canonical_hash(before_state) if before_state is not None else self.GENESIS
        after_hash = _canonical_hash(after_state) if after_state is not None else self.GENESIS
        prev_event = self.events[-1] if self.events else None
        prev_chain = prev_event.chain_hash if prev_event else self.GENESIS

        evt = AuditEvent(
            action=action,
            before_hash=before_hash,
            after_hash=after_hash,
            actor=actor,
            prev_event_id=prev_event.event_id if prev_event else None,
            metadata=dict(metadata or {}),
        )
        evt.chain_hash = _canonical_hash({
            "prev_chain": prev_chain,
            **evt._fields_for_chain(),
        })
        self.events.append(evt)
        return evt

    def verify_chain(self) -> dict:
        """Recompute the hash chain and return a verification report."""
        broken_at: Optional[int] = None
        prev_chain = self.GENESIS
        prev_event_id: Optional[str] = None
        prev_after_hash: Optional[str] = None

        for i, evt in enumerate(self.events):
            expected_chain = _canonical_hash({
                "prev_chain": prev_chain,
                **evt._fields_for_chain(),
            })
            if expected_chain != evt.chain_hash:
                broken_at = i
                break
            if evt.prev_event_id != prev_event_id:
                broken_at = i
                break
            # Continuity check: this event's before_hash should match the prior after_hash
            # once we're past the genesis event.
            if prev_after_hash is not None and evt.before_hash != prev_after_hash:
                broken_at = i
                break
            prev_chain = evt.chain_hash
            prev_event_id = evt.event_id
            prev_after_hash = evt.after_hash

        return {
            "valid": broken_at is None,
            "broken_at": broken_at,
            "events_checked": len(self.events),
            "head_chain_hash": self.events[-1].chain_hash if self.events else self.GENESIS,
        }

    def to_dict(self) -> dict:
        return {"events": [e.to_dict() for e in self.events]}
