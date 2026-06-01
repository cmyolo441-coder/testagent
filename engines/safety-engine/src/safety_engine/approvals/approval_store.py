"""Approval Store — Track approval requests and decisions"""
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from typing import Optional
import uuid


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"


@dataclass
class ApprovalRequest:
    id: str = field(default_factory=lambda: f"APR-{uuid.uuid4().hex[:8]}")
    action_type: str = ""  # command, file_write, file_delete, network, etc.
    action_description: str = ""
    risk_score: int = 0
    risk_level: str = "low"
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_by: str = "system"
    approved_by: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decided_at: Optional[str] = None
    expiry_seconds: int = 300  # 5 minutes
    context: dict = field(default_factory=dict)

    def approve(self, approver: str = "user"):
        self.status = ApprovalStatus.APPROVED
        self.approved_by = approver
        self.decided_at = datetime.now(timezone.utc).isoformat()

    def reject(self, approver: str = "user"):
        self.status = ApprovalStatus.REJECTED
        self.approved_by = approver
        self.decided_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action_type": self.action_type,
            "action_description": self.action_description,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "status": self.status.value,
            "requested_by": self.requested_by,
            "approved_by": self.approved_by,
            "created_at": self.created_at,
            "decided_at": self.decided_at,
            "context": self.context,
        }


class ApprovalStore:
    """In-memory approval store (SQLite-backed in production)."""

    def __init__(self):
        self.requests: dict[str, ApprovalRequest] = {}

    def request_approval(self, action_type: str, description: str,
                        risk_score: int, context: dict = None) -> ApprovalRequest:
        req = ApprovalRequest(
            action_type=action_type,
            action_description=description,
            risk_score=risk_score,
            risk_level=self._score_to_level(risk_score),
            context=context or {},
        )
        self.requests[req.id] = req
        return req

    def approve(self, request_id: str, approver: str = "user") -> bool:
        req = self.requests.get(request_id)
        if not req or req.status != ApprovalStatus.PENDING:
            return False
        req.approve(approver)
        return True

    def reject(self, request_id: str, approver: str = "user") -> bool:
        req = self.requests.get(request_id)
        if not req or req.status != ApprovalStatus.PENDING:
            return False
        req.reject(approver)
        return True

    def get_pending(self) -> list[ApprovalRequest]:
        return [r for r in self.requests.values() if r.status == ApprovalStatus.PENDING]

    def get_all(self) -> list[ApprovalRequest]:
        return list(self.requests.values())

    def get_by_id(self, request_id: str) -> Optional[ApprovalRequest]:
        return self.requests.get(request_id)

    def auto_approve_low_risk(self, max_score: int = 30):
        for req in self.requests.values():
            if req.status == ApprovalStatus.PENDING and req.risk_score <= max_score:
                req.status = ApprovalStatus.AUTO_APPROVED
                req.approved_by = "system"
                req.decided_at = datetime.now(timezone.utc).isoformat()

    def _score_to_level(self, score: int) -> str:
        if score >= 80: return "critical"
        if score >= 60: return "high"
        if score >= 40: return "medium"
        if score >= 20: return "low"
        return "safe"
