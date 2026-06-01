"""Epistemic Status Tracker — Track the epistemic status of knowledge claims"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid


class EpistemicStatus(Enum):
    CERTAIN = "certain"
    PROBABLE = "probable"
    POSSIBLE = "possible"
    DOUBTFUL = "doubtful"
    REFUTED = "refuted"
    UNKNOWN = "unknown"


class KnowledgeType(Enum):
    FACT = "fact"
    BELIEF = "belief"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    ASSUMPTION = "assumption"
    OBSERVATION = "observation"
    TESTIMONY = "testimony"


@dataclass
class EpistemicEntry:
    id: str = field(default_factory=lambda: f"EP-{uuid.uuid4().hex[:8]}")
    claim: str = ""
    status: EpistemicStatus = EpistemicStatus.UNKNOWN
    knowledge_type: KnowledgeType = KnowledgeType.BELIEF
    confidence: float = 0.5
    evidence_for: list[str] = field(default_factory=list)
    evidence_against: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    last_verified: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: str = ""

    @property
    def evidence_balance(self) -> float:
        total = len(self.evidence_for) + len(self.evidence_against)
        if total == 0:
            return 0.0
        return (len(self.evidence_for) - len(self.evidence_against)) / total

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "claim": self.claim,
            "status": self.status.value,
            "knowledge_type": self.knowledge_type.value,
            "confidence": self.confidence,
            "evidence_for_count": len(self.evidence_for),
            "evidence_against_count": len(self.evidence_against),
            "evidence_balance": round(self.evidence_balance, 2),
            "sources": self.sources,
            "last_verified": self.last_verified,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class EpistemicStatusTracker:
    """Track and manage epistemic status of knowledge claims."""

    def __init__(self):
        self.entries: dict[str, EpistemicEntry] = {}
        self.history: list[dict] = []

    def add_claim(self, claim: str, status: EpistemicStatus = EpistemicStatus.UNKNOWN,
                  knowledge_type: KnowledgeType = KnowledgeType.BELIEF,
                  confidence: float = 0.5, sources: list[str] = None) -> EpistemicEntry:
        entry = EpistemicEntry(
            claim=claim,
            status=status,
            knowledge_type=knowledge_type,
            confidence=min(max(confidence, 0), 1),
            sources=sources or [],
        )
        self.entries[entry.id] = entry
        self._record_change(entry.id, "created", {"claim": claim, "status": status.value})
        return entry

    def update_status(self, entry_id: str, new_status: EpistemicStatus,
                      reason: str = "") -> bool:
        entry = self.entries.get(entry_id)
        if not entry:
            return False
        old_status = entry.status
        entry.status = new_status
        entry.updated_at = datetime.now(timezone.utc).isoformat()
        self._record_change(entry_id, "status_change", {
            "old": old_status.value, "new": new_status.value, "reason": reason
        })
        return True

    def add_evidence(self, entry_id: str, evidence: str, is_supporting: bool = True) -> bool:
        entry = self.entries.get(entry_id)
        if not entry:
            return False
        if is_supporting:
            entry.evidence_for.append(evidence)
        else:
            entry.evidence_against.append(evidence)
        entry.updated_at = datetime.now(timezone.utc).isoformat()
        self._recalculate_status(entry)
        self._record_change(entry_id, "evidence_added", {
            "supporting": is_supporting, "count_for": len(entry.evidence_for),
            "count_against": len(entry.evidence_against),
        })
        return True

    def verify_claim(self, entry_id: str, verifier: str,
                     is_confirmed: bool) -> bool:
        entry = self.entries.get(entry_id)
        if not entry:
            return False
        entry.last_verified = datetime.now(timezone.utc).isoformat()
        entry.sources.append(verifier)
        if is_confirmed:
            entry.status = EpistemicStatus.PROBABLE
            entry.confidence = min(1.0, entry.confidence + 0.2)
        else:
            entry.status = EpistemicStatus.DOUBTFUL
            entry.confidence = max(0.0, entry.confidence - 0.3)
        entry.updated_at = datetime.now(timezone.utc).isoformat()
        self._record_change(entry_id, "verified", {
            "verifier": verifier, "confirmed": is_confirmed
        })
        return True

    def get_by_status(self, status: EpistemicStatus) -> list[EpistemicEntry]:
        return [e for e in self.entries.values() if e.status == status]

    def get_by_type(self, knowledge_type: KnowledgeType) -> list[EpistemicEntry]:
        return [e for e in self.entries.values() if e.knowledge_type == knowledge_type]

    def get_uncertain_claims(self, threshold: float = 0.5) -> list[EpistemicEntry]:
        return [e for e in self.entries.values() if e.confidence < threshold]

    def get_stale_claims(self, max_age_days: int = 30) -> list[EpistemicEntry]:
        now = datetime.now(timezone.utc)
        stale = []
        for entry in self.entries.values():
            if entry.last_verified:
                try:
                    verified_date = datetime.fromisoformat(entry.last_verified)
                    age_days = (now - verified_date).days
                    if age_days > max_age_days:
                        stale.append(entry)
                except (ValueError, TypeError):
                    pass
        return stale

    def get_epistemic_summary(self) -> dict:
        entries = list(self.entries.values())
        by_status = {}
        for e in entries:
            by_status[e.status.value] = by_status.get(e.status.value, 0) + 1
        by_type = {}
        for e in entries:
            by_type[e.knowledge_type.value] = by_type.get(e.knowledge_type.value, 0) + 1
        avg_confidence = sum(e.confidence for e in entries) / len(entries) if entries else 0
        return {
            "total_claims": len(entries),
            "by_status": by_status,
            "by_type": by_type,
            "avg_confidence": round(avg_confidence, 2),
            "uncertain": len([e for e in entries if e.confidence < 0.5]),
            "verified": len([e for e in entries if e.last_verified]),
        }

    def _recalculate_status(self, entry: EpistemicEntry):
        balance = entry.evidence_balance
        if balance > 0.5:
            entry.status = EpistemicStatus.PROBABLE
            entry.confidence = min(1.0, 0.5 + balance * 0.5)
        elif balance < -0.5:
            entry.status = EpistemicStatus.DOUBTFUL
            entry.confidence = max(0.0, 0.5 + balance * 0.5)
        elif balance > 0:
            entry.status = EpistemicStatus.POSSIBLE
        elif balance < 0:
            entry.status = EpistemicStatus.DOUBTFUL

    def _record_change(self, entry_id: str, change_type: str, details: dict):
        self.history.append({
            "entry_id": entry_id,
            "change_type": change_type,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
