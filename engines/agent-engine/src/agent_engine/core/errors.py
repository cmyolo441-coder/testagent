"""Agent Errors — Typed error hierarchy"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentError(Exception):
    message: str
    code: str = "AGENT_ERROR"
    details: dict = None
    recoverable: bool = True

    def __post_init__(self):
        super().__init__(self.message)
        if self.details is None:
            self.details = {}


@dataclass
class ToolError(AgentError):
    tool_name: str = ""
    tool_args: dict = None
    code: str = "TOOL_ERROR"

    def __post_init__(self):
        super().__post_init__()
        if self.tool_args is None:
            self.tool_args = {}


@dataclass
class SafetyError(AgentError):
    risk_score: int = 0
    blocked_action: str = ""
    code: str = "SAFETY_ERROR"
    recoverable: bool = False


@dataclass
class ApprovalRequiredError(AgentError):
    action_type: str = ""
    action_description: str = ""
    risk_score: int = 0
    code: str = "APPROVAL_REQUIRED"


@dataclass
class TimeoutError(AgentError):
    timeout_seconds: int = 0
    operation: str = ""
    code: str = "TIMEOUT_ERROR"


@dataclass
class QuotaExceededError(AgentError):
    resource: str = ""
    limit: int = 0
    current: int = 0
    code: str = "QUOTA_EXCEEDED"
    recoverable: bool = False


@dataclass
class ContextLimitError(AgentError):
    current_tokens: int = 0
    max_tokens: int = 0
    code: str = "CONTEXT_LIMIT_ERROR"


@dataclass
class ModelError(AgentError):
    model: str = ""
    provider: str = ""
    status_code: int = 0
    code: str = "MODEL_ERROR"


@dataclass
class ValidationError(AgentError):
    field: str = ""
    expected: str = ""
    got: str = ""
    code: str = "VALIDATION_ERROR"


class ErrorHandler:
    """Central error handler with recovery strategies."""

    def __init__(self):
        self.error_counts: dict[str, int] = {}
        self.max_retries: dict[str, int] = {
            "TOOL_ERROR": 3,
            "TIMEOUT_ERROR": 2,
            "MODEL_ERROR": 3,
            "CONTEXT_LIMIT_ERROR": 1,
        }

    def handle(self, error: AgentError) -> dict:
        code = error.code
        self.error_counts[code] = self.error_counts.get(code, 0) + 1

        max_retries = self.max_retries.get(code, 0)
        can_retry = self.error_counts[code] <= max_retries and error.recoverable

        return {
            "error_code": code,
            "message": error.message,
            "recoverable": error.recoverable,
            "can_retry": can_retry,
            "attempt": self.error_counts[code],
            "max_retries": max_retries,
            "details": error.details,
        }

    def should_stop(self, error: AgentError) -> bool:
        if not error.recoverable:
            return True
        code = error.code
        max_retries = self.max_retries.get(code, 0)
        return self.error_counts.get(code, 0) > max_retries

    def reset(self):
        self.error_counts.clear()
