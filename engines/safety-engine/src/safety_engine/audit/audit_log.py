"""Audit Log — Append-only immutable audit trail"""
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class AuditEvent:
    id: str = field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:12]}")
    event_type: str = ""  # command_executed, file_modified, approval_granted, etc.
    entity_type: str = ""  # mission, task, tool_call, etc.
    entity_id: str = ""
    actor: str = "system"
    details: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    prev_hash: Optional[str] = None
    event_hash: Optional[str] = None

    def compute_hash(self) -> str:
        data = f"{self.id}:{self.event_type}:{self.entity_type}:{self.entity_id}:{self.actor}:{self.timestamp}:{json.dumps(self.details, sort_keys=True)}"
        if self.prev_hash:
            data += f":{self.prev_hash}"
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "actor": self.actor,
            "details": self.details,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "event_hash": self.event_hash,
        }


class AuditLog:
    """Append-only audit log with hash chain for integrity."""

    def __init__(self):
        self.events: list[AuditEvent] = []
        self.last_hash: Optional[str] = None

    def log(self, event_type: str, entity_type: str, entity_id: str,
            actor: str = "system", details: dict = None) -> AuditEvent:
        event = AuditEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            details=details or {},
            prev_hash=self.last_hash,
        )
        event.event_hash = event.compute_hash()
        self.last_hash = event.event_hash
        self.events.append(event)
        return event

    def verify_integrity(self) -> tuple[bool, Optional[str]]:
        prev_hash = None
        for i, event in enumerate(self.events):
            if event.prev_hash != prev_hash:
                return False, f"Chain broken at event {i}: {event.id}"
            expected_hash = event.compute_hash()
            if event.event_hash != expected_hash:
                return False, f"Hash mismatch at event {i}: {event.id}"
            prev_hash = event.event_hash
        return True, None

    def get_events(self, entity_type: str = None, entity_id: str = None,
                   event_type: str = None, limit: int = 100) -> list[AuditEvent]:
        filtered = self.events
        if entity_type:
            filtered = [e for e in filtered if e.entity_type == entity_type]
        if entity_id:
            filtered = [e for e in filtered if e.entity_id == entity_id]
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        return filtered[-limit:]

    def get_stats(self) -> dict:
        types = {}
        for e in self.events:
            types[e.event_type] = types.get(e.event_type, 0) + 1
        return {
            "total_events": len(self.events),
            "event_types": types,
            "chain_valid": self.verify_integrity()[0],
        }
