"""Approval Audit — Log and verify approval decisions"""
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class ApprovalAuditRecord:
    id: str = field(default_factory=lambda: f"AUD-{uuid.uuid4().hex[:8]}")
    request_id: str = ""
    action_type: str = ""
    action_description: str = ""
    risk_score: int = 0
    risk_level: str = ""
    decision: str = ""  # approved, rejected, deferred, auto_approved, auto_rejected
    approver: str = ""
    reason: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    session_id: str = ""
    ip_address: str = ""
    metadata: dict = field(default_factory=dict)
    record_hash: Optional[str] = None
    prev_hash: Optional[str] = None

    def compute_hash(self) -> str:
        data = (
            f"{self.id}:{self.request_id}:{self.action_type}:"
            f"{self.decision}:{self.approver}:{self.timestamp}:"
            f"{json.dumps(self.metadata, sort_keys=True)}"
        )
        if self.prev_hash:
            data += f":{self.prev_hash}"
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "request_id": self.request_id,
            "action_type": self.action_type,
            "action_description": self.action_description,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "decision": self.decision,
            "approver": self.approver,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "metadata": self.metadata,
            "record_hash": self.record_hash,
            "prev_hash": self.prev_hash,
        }


class ApprovalAudit:
    """Audit trail for all approval decisions with hash chain integrity."""

    def __init__(self):
        self.records: list[ApprovalAuditRecord] = []
        self.last_hash: Optional[str] = None
        self._decision_stats: dict[str, int] = {
            "approved": 0, "rejected": 0, "deferred": 0,
            "auto_approved": 0, "auto_rejected": 0,
        }

    def log(self, request_id: str, action_type: str, action_description: str,
            risk_score: int, risk_level: str, decision: str, approver: str,
            reason: str = "", session_id: str = "", ip_address: str = "",
            metadata: dict = None) -> ApprovalAuditRecord:
        record = ApprovalAuditRecord(
            request_id=request_id,
            action_type=action_type,
            action_description=action_description,
            risk_score=risk_score,
            risk_level=risk_level,
            decision=decision,
            approver=approver,
            reason=reason,
            session_id=session_id,
            ip_address=ip_address,
            metadata=metadata or {},
            prev_hash=self.last_hash,
        )
        record.record_hash = record.compute_hash()
        self.last_hash = record.record_hash
        self.records.append(record)

        if decision in self._decision_stats:
            self._decision_stats[decision] += 1

        return record

    def verify_integrity(self) -> tuple[bool, Optional[str]]:
        prev_hash = None
        for i, record in enumerate(self.records):
            if record.prev_hash != prev_hash:
                return False, f"Chain broken at record {i}: {record.id}"
            expected_hash = record.compute_hash()
            if record.record_hash != expected_hash:
                return False, f"Hash mismatch at record {i}: {record.id}"
            prev_hash = record.record_hash
        return True, None

    def get_records(self, decision: str = None, approver: str = None,
                    action_type: str = None, limit: int = 100) -> list[ApprovalAuditRecord]:
        filtered = self.records
        if decision:
            filtered = [r for r in filtered if r.decision == decision]
        if approver:
            filtered = [r for r in filtered if r.approver == approver]
        if action_type:
            filtered = [r for r in filtered if r.action_type == action_type]
        return filtered[-limit:]

    def get_stats(self) -> dict:
        return {
            "total_records": len(self.records),
            "decisions": dict(self._decision_stats),
            "approval_rate": (
                self._decision_stats["approved"] / max(1, sum(self._decision_stats.values()))
            ),
            "chain_valid": self.verify_integrity()[0],
            "unique_approvers": len(set(r.approver for r in self.records)),
        }

    def export_audit_trail(self) -> list[dict]:
        return [r.to_dict() for r in self.records]
