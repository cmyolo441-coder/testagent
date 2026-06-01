"""Approval UI — Interface for presenting approval requests to users"""
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from safety_engine.approvals.approval_store import ApprovalRequest, ApprovalStatus


@dataclass
class UIPresentation:
    request_id: str
    action_type: str
    description: str
    risk_score: int
    risk_level: str
    reasons: list[str]
    timestamp: str
    formatted_message: str
    options: list[str]

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "action_type": self.action_type,
            "description": self.description,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "reasons": self.reasons,
            "timestamp": self.timestamp,
            "options": self.options,
        }


@dataclass
class UIPromptResult:
    decision: str  # "approve", "reject", "defer"
    approver: str
    reason: str
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "approver": self.approver,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


class ApprovalUI:
    """Present approval requests and collect user decisions."""

    RISK_COLORS = {
        "safe": "\033[92m",     # green
        "low": "\033[93m",      # yellow
        "medium": "\033[33m",   # orange
        "high": "\033[91m",     # red
        "critical": "\033[31m", # dark red
    }
    RESET_COLOR = "\033[0m"

    def __init__(self, use_color: bool = True, interactive: bool = True):
        self.use_color = use_color
        self.interactive = interactive
        self.decision_history: list[UIPromptResult] = []

    def present(self, request: ApprovalRequest) -> UIPresentation:
        reasons_text = "\n".join(f"  - {r}" for r in (request.context.get("reasons", []) or []))

        options = []
        if request.risk_level in ("critical", "high"):
            options = ["approve", "reject"]
        elif request.risk_level == "medium":
            options = ["approve", "reject", "defer"]
        else:
            options = ["approve", "reject", "defer"]

        msg = self._format_message(request, reasons_text, options)

        return UIPresentation(
            request_id=request.id,
            action_type=request.action_type,
            description=request.action_description,
            risk_score=request.risk_score,
            risk_level=request.risk_level,
            reasons=request.context.get("reasons", []),
            timestamp=datetime.now(timezone.utc).isoformat(),
            formatted_message=msg,
            options=options,
        )

    def prompt(self, request: ApprovalRequest) -> UIPromptResult:
        presentation = self.present(request)

        if not self.interactive:
            auto = self._auto_decide(request)
            return auto

        print(presentation.formatted_message)

        while True:
            try:
                choice = input("\nDecision [approve/reject/defer]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                choice = "reject"

            if choice in presentation.options:
                result = UIPromptResult(
                    decision=choice,
                    approver="user",
                    reason=f"User selected {choice}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                self.decision_history.append(result)
                return result
            print(f"Invalid choice. Options: {', '.join(presentation.options)}")

    def prompt_batch(self, requests: list[ApprovalRequest]) -> dict[str, UIPromptResult]:
        results = {}
        for req in requests:
            results[req.id] = self.prompt(req)
        return results

    def _auto_decide(self, request: ApprovalRequest) -> UIPromptResult:
        if request.risk_level in ("safe", "low"):
            decision = "approve"
            reason = f"Auto-approved: {request.risk_level} risk"
        elif request.risk_level == "critical":
            decision = "reject"
            reason = "Auto-rejected: critical risk"
        else:
            decision = "reject"
            reason = "Non-interactive mode: cannot approve medium/high risk"

        result = UIPromptResult(
            decision=decision,
            approver="system",
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.decision_history.append(result)
        return result

    def _format_message(self, request: ApprovalRequest, reasons_text: str,
                        options: list[str]) -> str:
        color = self.RISK_COLORS.get(request.risk_level, "")
        reset = self.RESET_COLOR if self.use_color else ""

        lines = [
            f"\n{'='*60}",
            f"  {color}APPROVAL REQUEST{reset}",
            f"{'='*60}",
            f"  ID:          {request.id}",
            f"  Action:      {request.action_type}",
            f"  Description: {request.action_description}",
            f"  Risk Score:  {color}{request.risk_score}/100{reset}",
            f"  Risk Level:  {color}{request.risk_level.upper()}{reset}",
            f"  Requested:   {request.created_at}",
        ]

        if reasons_text:
            lines.append(f"\n  Reasons:")
            lines.append(reasons_text)

        lines.append(f"\n  Options: {', '.join(options)}")
        lines.append(f"{'='*60}\n")

        return "\n".join(lines)

    def get_history(self) -> list[UIPromptResult]:
        return list(self.decision_history)
