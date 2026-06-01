"""Risk Approval Screen — Approval queue and risk display"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ApprovalRequest:
    id: str = ""
    title: str = ""
    description: str = ""
    request_type: str = ""  # tool_execution, code_change, deployment, data_access
    status: str = "pending"  # pending, approved, rejected, expired
    risk_level: str = "medium"  # low, medium, high, critical
    risk_score: float = 0.5
    requested_by: str = ""
    approver: Optional[str] = None
    context: dict = field(default_factory=dict)
    conditions: list[str] = field(default_factory=list)
    expiry_minutes: int = 60
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decided_at: Optional[str] = None


@dataclass
class RiskAssessment:
    request_id: str
    risk_factors: list[str] = field(default_factory=list)
    mitigation_steps: list[str] = field(default_factory=list)
    overall_risk: float = 0.5
    recommendation: str = ""  # approve, reject, review
    assessor: str = ""


class RiskApprovalScreen:
    """Approval queue and risk display screen."""

    TITLE = "Risk Approval"

    def __init__(self):
        self.requests: dict[str, ApprovalRequest] = {}
        self.assessments: dict[str, RiskAssessment] = {}
        self.selected_request_id: Optional[str] = None

    def submit_request(self, title: str, description: str = "",
                       request_type: str = "tool_execution",
                       risk_level: str = "medium", risk_score: float = 0.5,
                       requested_by: str = "", context: dict = None,
                       conditions: list[str] = None,
                       expiry_minutes: int = 60, tags: list[str] = None) -> ApprovalRequest:
        req_id = f"APR-{len(self.requests) + 1:04d}"
        request = ApprovalRequest(
            id=req_id,
            title=title,
            description=description,
            request_type=request_type,
            risk_level=risk_level,
            risk_score=risk_score,
            requested_by=requested_by,
            context=context or {},
            conditions=conditions or [],
            expiry_minutes=expiry_minutes,
            tags=tags or [],
        )
        self.requests[req_id] = request
        return request

    def assess_risk(self, request_id: str, risk_factors: list[str] = None,
                    mitigation_steps: list[str] = None,
                    overall_risk: float = 0.5,
                    recommendation: str = "review",
                    assessor: str = "") -> Optional[RiskAssessment]:
        if request_id not in self.requests:
            return None
        assessment = RiskAssessment(
            request_id=request_id,
            risk_factors=risk_factors or [],
            mitigation_steps=mitigation_steps or [],
            overall_risk=overall_risk,
            recommendation=recommendation,
            assessor=assessor,
        )
        self.assessments[request_id] = assessment
        return assessment

    def approve_request(self, request_id: str, approver: str = "",
                        notes: str = "") -> Optional[ApprovalRequest]:
        request = self.requests.get(request_id)
        if not request or request.status != "pending":
            return None
        request.status = "approved"
        request.approver = approver
        request.decided_at = datetime.now(timezone.utc).isoformat()
        return request

    def reject_request(self, request_id: str, approver: str = "",
                       reason: str = "") -> Optional[ApprovalRequest]:
        request = self.requests.get(request_id)
        if not request or request.status != "pending":
            return None
        request.status = "rejected"
        request.approver = approver
        request.decided_at = datetime.now(timezone.utc).isoformat()
        return request

    def get_pending_requests(self) -> list[ApprovalRequest]:
        return [r for r in self.requests.values() if r.status == "pending"]

    def get_high_risk_pending(self) -> list[ApprovalRequest]:
        return [r for r in self.get_pending_requests() if r.risk_level in ("high", "critical")]

    def get_approved_requests(self) -> list[ApprovalRequest]:
        return [r for r in self.requests.values() if r.status == "approved"]

    def get_rejected_requests(self) -> list[ApprovalRequest]:
        return [r for r in self.requests.values() if r.status == "rejected"]

    def get_risk_distribution(self) -> dict[str, int]:
        pending = self.get_pending_requests()
        dist = {}
        for r in pending:
            dist[r.risk_level] = dist.get(r.risk_level, 0) + 1
        return dist

    def get_approval_rate(self) -> float:
        all_decided = [r for r in self.requests.values() if r.status in ("approved", "rejected")]
        if not all_decided:
            return 1.0
        approved = sum(1 for r in all_decided if r.status == "approved")
        return approved / len(all_decided)

    def render_header(self) -> str:
        total = len(self.requests)
        pending = len(self.get_pending_requests())
        high_risk = len(self.get_high_risk_pending())
        return f"╔══════════════════════════════════════════════════════════╗\n║ RISK APPROVAL — {total} requests ({pending} pending, {high_risk} high-risk){'':<6}║\n╚══════════════════════════════════════════════════════════╝"

    def render_approval_queue(self) -> str:
        lines = ["┌─ Approval Queue ────────────────────────────────────┐"]
        risk_colors = {"critical": "!", "high": "H", "medium": "M", "low": "L"}
        for r in self.get_pending_requests()[:6]:
            risk_icon = risk_colors.get(r.risk_level, "?")
            lines.append(f"│ [{risk_icon}] {r.title[:30]:<30} {r.request_type:<12} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_risk_distribution(self) -> str:
        dist = self.get_risk_distribution()
        lines = [
            "┌─ Risk Distribution ─────────────────────────────────┐",
            f"│ Critical: {dist.get('critical', 0):<40} │",
            f"│ High:     {dist.get('high', 0):<40} │",
            f"│ Medium:   {dist.get('medium', 0):<40} │",
            f"│ Low:      {dist.get('low', 0):<40} │",
            f"│ Approval rate: {self.get_approval_rate():.1%}{'':<33} │",
            "└────────────────────────────────────────────────────┘",
        ]
        return "\n".join(lines)

    def render_full(self) -> str:
        parts = [
            self.render_header(),
            "",
            self.render_approval_queue(),
            "",
            self.render_risk_distribution(),
        ]
        return "\n".join(parts)

    def get_stats(self) -> dict:
        requests = list(self.requests.values())
        return {
            "total_requests": len(requests),
            "pending": len(self.get_pending_requests()),
            "approved": len(self.get_approved_requests()),
            "rejected": len(self.get_rejected_requests()),
            "high_risk": len(self.get_high_risk_pending()),
            "approval_rate": self.get_approval_rate(),
        }
