"""Truth Ledger — Append-only ledger for truth records"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid
import hashlib
import json


@dataclass
class LedgerEntry:
    id: str = field(default_factory=lambda: f"LED-{uuid.uuid4().hex[:8]}")
    claim: str = ""
    truth_value: bool = False
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    source: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    previous_hash: str = ""
    hash: str = ""
    metadata: dict = field(default_factory=dict)
    is_retracted: bool = False

    def compute_hash(self) -> str:
        data = {
            "claim": self.claim,
            "truth_value": self.truth_value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "source": self.source,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
        }
        data_str = json.dumps(data, sort_keys=True)
        self.hash = hashlib.sha256(data_str.encode()).hexdigest()
        return self.hash

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "claim": self.claim,
            "truth_value": self.truth_value,
            "confidence": self.confidence,
            "evidence_count": len(self.evidence),
            "source": self.source,
            "timestamp": self.timestamp,
            "hash": self.hash,
            "previous_hash": self.previous_hash,
            "retracted": self.is_retracted,
        }


class TruthLedger:
    """Append-only ledger for recording truth claims with chain verification."""

    def __init__(self):
        self.entries: list[LedgerEntry] = []
        self._index: dict[str, LedgerEntry] = {}
        self._chain_valid = True

    def record(self, claim: str, truth_value: bool, confidence: float,
               evidence: list[str] = None, source: str = "") -> LedgerEntry:
        previous_hash = self.entries[-1].hash if self.entries else "genesis"
        entry = LedgerEntry(
            claim=claim,
            truth_value=truth_value,
            confidence=min(max(confidence, 0), 1),
            evidence=evidence or [],
            source=source,
            previous_hash=previous_hash,
        )
        entry.compute_hash()
        self.entries.append(entry)
        self._index[entry.id] = entry
        return entry

    def retract(self, entry_id: str, reason: str = "") -> bool:
        entry = self._index.get(entry_id)
        if not entry:
            return False
        entry.is_retracted = True
        entry.metadata["retraction_reason"] = reason
        entry.metadata["retracted_at"] = datetime.now(timezone.utc).isoformat()
        return True

    def query(self, claim_substring: str) -> list[LedgerEntry]:
        return [e for e in self.entries
                if claim_substring.lower() in e.claim.lower() and not e.is_retracted]

    def query_by_source(self, source: str) -> list[LedgerEntry]:
        return [e for e in self.entries
                if e.source == source and not e.is_retracted]

    def query_by_confidence(self, min_confidence: float = 0.0,
                            max_confidence: float = 1.0) -> list[LedgerEntry]:
        return [e for e in self.entries
                if min_confidence <= e.confidence <= max_confidence and not e.is_retracted]

    def get_truth_value(self, claim: str) -> Optional[bool]:
        matches = self.query(claim)
        if not matches:
            return None
        latest = matches[-1]
        return latest.truth_value

    def verify_chain(self) -> bool:
        if not self.entries:
            return True
        for i in range(1, len(self.entries)):
            if self.entries[i].previous_hash != self.entries[i - 1].hash:
                self._chain_valid = False
                return False
        self._chain_valid = True
        return True

    def get_entry_count(self) -> int:
        return len([e for e in self.entries if not e.is_retracted])

    def get_retracted_count(self) -> int:
        return len([e for e in self.entries if e.is_retracted])

    def get_statistics(self) -> dict:
        active = [e for e in self.entries if not e.is_retracted]
        true_count = sum(1 for e in active if e.truth_value)
        false_count = sum(1 for e in active if not e.truth_value)
        avg_confidence = sum(e.confidence for e in active) / len(active) if active else 0
        sources = set(e.source for e in active if e.source)
        return {
            "total_entries": len(self.entries),
            "active_entries": len(active),
            "retracted_entries": self.get_retracted_count(),
            "true_claims": true_count,
            "false_claims": false_count,
            "avg_confidence": round(avg_confidence, 3),
            "unique_sources": len(sources),
            "chain_valid": self._chain_valid,
            "first_entry": self.entries[0].timestamp if self.entries else None,
            "last_entry": self.entries[-1].timestamp if self.entries else None,
        }

    def export_entries(self, start_idx: int = 0, end_idx: int = None) -> list[dict]:
        end = end_idx or len(self.entries)
        return [e.to_dict() for e in self.entries[start_idx:end]]

    def get_recent(self, count: int = 10) -> list[LedgerEntry]:
        return self.entries[-count:]

    def to_dict(self) -> dict:
        return {
            "entry_count": len(self.entries),
            "chain_valid": self._chain_valid,
            "statistics": self.get_statistics(),
            "recent_entries": [e.to_dict() for e in self.entries[-5:]],
        }
