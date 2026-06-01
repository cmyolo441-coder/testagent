"""Tool Runtime — Execute tools with safety checks and audit"""
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime, timezone
import uuid


@dataclass
class ToolResult:
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0
    tool_name: str = ""
    arguments: dict = field(default_factory=dict)
    risk_score: int = 0
    approval_required: bool = False
    approved: bool = True
    artifacts: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": str(self.output)[:500] if self.output else None,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "tool_name": self.tool_name,
            "risk_score": self.risk_score,
            "approved": self.approved,
        }


class ToolRuntime:
    """Execute tools with safety checks, timing, and audit."""

    def __init__(self, registry, risk_assessor=None, approval_store=None, audit_log=None):
        self.registry = registry
        self.risk_assessor = risk_assessor
        self.approval_store = approval_store
        self.audit_log = audit_log
        self.execution_history: list[ToolResult] = []

    def execute(self, tool_name: str, arguments: dict, dry_run: bool = False) -> ToolResult:
        tool_def = self.registry.get(tool_name)
        if not tool_def:
            return ToolResult(
                success=False,
                error=f"Unknown tool: {tool_name}",
                tool_name=tool_name,
                arguments=arguments,
            )

        if not tool_def.enabled:
            return ToolResult(
                success=False,
                error=f"Tool disabled: {tool_name}",
                tool_name=tool_name,
                arguments=arguments,
            )

        # Risk assessment
        risk_score = 0
        if self.risk_assessor:
            risk_score = self.risk_assessor.assess_command(f"{tool_name} {arguments}")

        # Approval check
        approval_required = tool_def.requires_approval or risk_score >= 60
        approved = True
        if approval_required and self.approval_store:
            req = self.approval_store.request_approval(
                action_type=tool_name,
                description=f"Execute {tool_name} with {arguments}",
                risk_score=risk_score,
            )
            approved = req.status.value == "approved"

        if dry_run:
            return ToolResult(
                success=True,
                output=f"DRY RUN: Would execute {tool_name}({arguments})",
                tool_name=tool_name,
                arguments=arguments,
                risk_score=risk_score,
                approval_required=approval_required,
                approved=approved,
            )

        if approval_required and not approved:
            return ToolResult(
                success=False,
                error="Approval required but not granted",
                tool_name=tool_name,
                arguments=arguments,
                risk_score=risk_score,
                approval_required=True,
                approved=False,
            )

        # Execute
        start_time = time.time()
        try:
            result = tool_def.handler(**arguments)
            duration = (time.time() - start_time) * 1000

            tool_result = ToolResult(
                success=True,
                output=result,
                duration_ms=duration,
                tool_name=tool_name,
                arguments=arguments,
                risk_score=risk_score,
                approval_required=approval_required,
                approved=approved,
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            tool_result = ToolResult(
                success=False,
                error=str(e),
                duration_ms=duration,
                tool_name=tool_name,
                arguments=arguments,
                risk_score=risk_score,
            )

        # Audit
        if self.audit_log:
            self.audit_log.log(
                event_type="tool_executed" if tool_result.success else "tool_failed",
                entity_type="tool_call",
                entity_id=f"{tool_name}-{uuid.uuid4().hex[:8]}",
                details=tool_result.to_dict(),
            )

        self.execution_history.append(tool_result)
        return tool_result

    def get_history(self, tool_name: str = None, limit: int = 20) -> list[ToolResult]:
        history = self.execution_history
        if tool_name:
            history = [r for r in history if r.tool_name == tool_name]
        return history[-limit:]

    def get_stats(self) -> dict:
        total = len(self.execution_history)
        success = sum(1 for r in self.execution_history if r.success)
        return {
            "total_executions": total,
            "successful": success,
            "failed": total - success,
            "success_rate": success / total if total > 0 else 0,
            "avg_duration_ms": sum(r.duration_ms for r in self.execution_history) / total if total > 0 else 0,
        }
