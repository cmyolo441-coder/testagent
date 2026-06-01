"""Approval Flow — Manage approval workflows for tool execution"""
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class ApprovalRequest:
    request_id: str = field(default_factory=lambda: f"REQ-{uuid.uuid4().hex[:8]}")
    tool_name: str = ""
    arguments: dict = field(default_factory=dict)
    risk_score: int = 0
    risk_level: str = "low"
    requester: str = "agent"
    reason: str = ""
    status: str = "pending"  # pending, approved, rejected, expired, deferred
    approver: str = ""
    decision_reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decided_at: str = ""
    expires_at: float = 0.0
    metadata: dict = field(default_factory=dict)

    def approve(self, approver: str = "user", reason: str = "Approved"):
        self.status = "approved"
        self.approver = approver
        self.decision_reason = reason
        self.decided_at = datetime.now(timezone.utc).isoformat()

    def reject(self, approver: str = "user", reason: str = "Rejected"):
        self.status = "rejected"
        self.approver = approver
        self.decision_reason = reason
        self.decided_at = datetime.now(timezone.utc).isoformat()

    def is_expired(self) -> bool:
        if self.expires_at <= 0:
            return False
        return time.time() > self.expires_at

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "requester": self.requester,
            "status": self.status,
            "approver": self.approver,
            "decision_reason": self.decision_reason,
            "created_at": self.created_at,
            "decided_at": self.decided_at,
        }


@dataclass
class ApprovalConfig:
    auto_approve_below: int = 30
    auto_reject_above: int = 95
    timeout_sec: int = 300
    require_reason_above: int = 70
    allow_defer: bool = True
    max_pending: int = 10


class ApprovalFlow:
    """Manage approval workflows for tool execution."""

    def __init__(self, config: ApprovalConfig = None):
        self.config = config or ApprovalConfig()
        self._requests: dict[str, ApprovalRequest] = {}
        self._history: list[ApprovalRequest] = []
        self._auto_approve_tools: set[str] = set()
        self._always_approve_tools: set[str] = set()

    def request(self, tool_name: str, arguments: dict, risk_score: int,
                requester: str = "agent", reason: str = "") -> ApprovalRequest:
        risk_level = self._score_to_level(risk_score)

        if tool_name in self._always_approve_tools:
            req = ApprovalRequest(
                tool_name=tool_name,
                arguments=arguments,
                risk_score=risk_score,
                risk_level=risk_level,
                requester=requester,
                reason=reason,
                status="approved",
                approver="system",
                decision_reason="Auto-approved (always approve list)",
            )
            self._history.append(req)
            return req

        if risk_score < self.config.auto_approve_below or tool_name in self._auto_approve_tools:
            req = ApprovalRequest(
                tool_name=tool_name,
                arguments=arguments,
                risk_score=risk_score,
                risk_level=risk_level,
                requester=requester,
                reason=reason,
                status="approved",
                approver="system",
                decision_reason=f"Auto-approved (score {risk_score} < {self.config.auto_approve_below})",
            )
            self._history.append(req)
            return req

        if risk_score >= self.config.auto_reject_above:
            req = ApprovalRequest(
                tool_name=tool_name,
                arguments=arguments,
                risk_score=risk_score,
                risk_level=risk_level,
                requester=requester,
                reason=reason,
                status="rejected",
                approver="system",
                decision_reason=f"Auto-rejected (score {risk_score} >= {self.config.auto_reject_above})",
            )
            self._history.append(req)
            return req

        pending_count = sum(1 for r in self._requests.values() if r.status == "pending")
        if pending_count >= self.config.max_pending:
            req = ApprovalRequest(
                tool_name=tool_name,
                arguments=arguments,
                risk_score=risk_score,
                risk_level=risk_level,
                requester=requester,
                reason=reason,
                status="rejected",
                approver="system",
                decision_reason=f"Rejected: too many pending requests ({pending_count})",
            )
            self._history.append(req)
            return req

        req = ApprovalRequest(
            tool_name=tool_name,
            arguments=arguments,
            risk_score=risk_score,
            risk_level=risk_level,
            requester=requester,
            reason=reason,
            expires_at=time.time() + self.config.timeout_sec,
        )
        self._requests[req.request_id] = req
        return req

    def decide(self, request_id: str, approved: bool,
               approver: str = "user", reason: str = "") -> Optional[ApprovalRequest]:
        req = self._requests.get(request_id)
        if not req or req.status != "pending":
            return None

        if approved:
            req.approve(approver, reason or "Approved by user")
        else:
            req.reject(approver, reason or "Rejected by user")

        self._history.append(req)
        del self._requests[request_id]
        return req

    def get_pending(self) -> list[ApprovalRequest]:
        self._expire_old()
        return [r for r in self._requests.values() if r.status == "pending"]

    def get_history(self, tool_name: str = None, limit: int = 50) -> list[ApprovalRequest]:
        history = self._history
        if tool_name:
            history = [r for r in history if r.tool_name == tool_name]
        return history[-limit:]

    def approve_tool(self, tool_name: str):
        self._always_approve_tools.add(tool_name)

    def auto_approve_tool(self, tool_name: str):
        self._auto_approve_tools.add(tool_name)

    def _expire_old(self):
        now = time.time()
        expired = [rid for rid, r in self._requests.items() if r.is_expired()]
        for rid in expired:
            req = self._requests.pop(rid)
            req.status = "expired"
            req.decision_reason = "Expired"
            req.decided_at = datetime.now(timezone.utc).isoformat()
            self._history.append(req)

    def _score_to_level(self, score: int) -> str:
        if score >= 80:
            return "critical"
        if score >= 60:
            return "high"
        if score >= 40:
            return "medium"
        if score >= 20:
            return "low"
        return "safe"
