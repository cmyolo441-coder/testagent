"""Immutable Store — Append-only event storage with tamper detection"""
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional
import uuid


@dataclass
class StoredEvent:
    id: str = field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:12]}")
    event_type: str = ""
    source: str = ""
    payload: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    sequence: int = 0
    prev_hash: str = ""
    event_hash: str = ""
    signatures: list[dict] = field(default_factory=list)

    def compute_hash(self) -> str:
        data = (
            f"{self.id}:{self.event_type}:{self.source}:"
            f"{json.dumps(self.payload, sort_keys=True, default=str)}:"
            f"{self.timestamp}:{self.sequence}:{self.prev_hash}"
        )
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "source": self.source,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
            "prev_hash": self.prev_hash,
            "event_hash": self.event_hash,
            "signatures": self.signatures,
        }


class ImmutableStore:
    """Append-only immutable event store with hash chain integrity."""

    def __init__(self, name: str = "default"):
        self.name = name
        self.events: list[StoredEvent] = []
        self._index: dict[str, StoredEvent] = {}
        self._type_index: dict[str, list[StoredEvent]] = {}
        self._source_index: dict[str, list[StoredEvent]] = {}
        self._last_hash: str = ""
        self._sequence: int = 0

    def store(self, event_type: str, source: str, payload: dict,
              signatures: list[dict] = None) -> StoredEvent:
        self._sequence += 1
        event = StoredEvent(
            event_type=event_type,
            source=source,
            payload=payload,
            timestamp=time.time(),
            sequence=self._sequence,
            prev_hash=self._last_hash,
            signatures=signatures or [],
        )
        event.event_hash = event.compute_hash()
        self._last_hash = event.event_hash

        self.events.append(event)
        self._index[event.id] = event

        if event_type not in self._type_index:
            self._type_index[event_type] = []
        self._type_index[event_type].append(event)

        if source not in self._source_index:
            self._source_index[source] = []
        self._source_index[source].append(event)

        return event

    def get(self, event_id: str) -> Optional[StoredEvent]:
        return self._index.get(event_id)

    def query(self, event_type: str = None, source: str = None,
              since: float = None, until: float = None,
              limit: int = 100) -> list[StoredEvent]:
        if event_type and event_type in self._type_index:
            results = list(self._type_index[event_type])
        elif source and source in self._source_index:
            results = list(self._source_index[source])
        else:
            results = list(self.events)

        if since:
            results = [e for e in results if e.timestamp >= since]
        if until:
            results = [e for e in results if e.timestamp <= until]

        return results[-limit:]

    def verify_integrity(self) -> tuple[bool, Optional[str]]:
        prev_hash = ""
        for i, event in enumerate(self.events):
            if event.prev_hash != prev_hash:
                return False, f"Chain broken at index {i}, event {event.id}"
            expected_hash = event.compute_hash()
            if event.event_hash != expected_hash:
                return False, f"Hash mismatch at index {i}, event {event.id}"
            prev_hash = event.event_hash
        return True, None

    def get_events(self, limit: int = 100, offset: int = 0) -> list[StoredEvent]:
        return self.events[offset:offset + limit]

    def count(self, event_type: str = None) -> int:
        if event_type and event_type in self._type_index:
            return len(self._type_index[event_type])
        return len(self.events)

    def export(self) -> list[dict]:
        return [e.to_dict() for e in self.events]
