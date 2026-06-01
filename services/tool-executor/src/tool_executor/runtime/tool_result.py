"""Tool Result — Structured result type for tool execution"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class ToolResult:
    """Structured result type for all tool executions."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    error_code: str = ""
    tool_name: str = ""
    arguments: dict = field(default_factory=dict)
    duration_ms: float = 0.0
    risk_score: int = 0
    approval_required: bool = False
    approved: bool = True
    sandbox_used: bool = False
    artifacts: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    request_id: str = ""
    execution_id: str = ""

    def to_dict(self) -> dict:
        result = {
            "success": self.success,
            "tool_name": self.tool_name,
            "duration_ms": self.duration_ms,
            "risk_score": self.risk_score,
            "approved": self.approved,
            "timestamp": self.timestamp,
        }
        if self.data is not None:
            data_str = str(self.data)
            result["data"] = self.data if len(data_str) < 5000 else data_str[:5000] + "..."
        if self.error:
            result["error"] = self.error
            result["error_code"] = self.error_code
        if self.artifacts:
            result["artifacts"] = self.artifacts
        return result

    @classmethod
    def success(cls, data: Any, tool_name: str = "", **kwargs) -> "ToolResult":
        return cls(success=True, data=data, tool_name=tool_name, **kwargs)

    @classmethod
    def error(cls, error: str, tool_name: str = "", error_code: str = "", **kwargs) -> "ToolResult":
        return cls(success=False, error=error, error_name=error_code, tool_name=tool_name, **kwargs)

    @classmethod
    def from_exception(cls, exc: Exception, tool_name: str = "", **kwargs) -> "ToolResult":
        return cls(
            success=False,
            error=str(exc),
            error_code=type(exc).__name__,
            tool_name=tool_name,
            **kwargs,
        )

    def add_artifact(self, name: str, artifact_type: str, data: Any, path: str = ""):
        self.artifacts.append({
            "name": name,
            "type": artifact_type,
            "data": str(data)[:1000],
            "path": path,
        })

    def set_metadata(self, key: str, value: Any):
        self.metadata[key] = value

    def is_timeout(self) -> bool:
        return self.error_code == "TimeoutError"

    def is_permission_denied(self) -> bool:
        return self.error_code == "PermissionError"

    def needs_approval(self) -> bool:
        return self.approval_required and not self.approved
