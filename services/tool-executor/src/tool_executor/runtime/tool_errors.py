"""Tool Errors — Exception hierarchy for tool execution"""
from typing import Any, Optional


class ToolError(Exception):
    """Base exception for all tool errors."""

    def __init__(self, message: str, tool_name: str = "",
                 error_code: str = "", details: dict = None):
        super().__init__(message)
        self.message = message
        self.tool_name = tool_name
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "error": self.message,
            "error_code": self.error_code,
            "tool_name": self.tool_name,
            "details": self.details,
        }

    def __str__(self) -> str:
        if self.tool_name:
            return f"[{self.tool_name}] {self.message}"
        return self.message


class ToolTimeoutError(ToolError):
    """Raised when a tool execution exceeds its time limit."""

    def __init__(self, message: str = "Tool execution timed out",
                 tool_name: str = "", timeout_sec: int = 0, **kwargs):
        super().__init__(message, tool_name, error_code="TimeoutError", **kwargs)
        self.timeout_sec = timeout_sec


class ToolPermissionError(ToolError):
    """Raised when a tool lacks required permissions."""

    def __init__(self, message: str = "Permission denied",
                 tool_name: str = "", required_permission: str = "", **kwargs):
        super().__init__(message, tool_name, error_code="PermissionError", **kwargs)
        self.required_permission = required_permission


class ToolValidationError(ToolError):
    """Raised when tool input validation fails."""

    def __init__(self, message: str = "Input validation failed",
                 tool_name: str = "", validation_errors: list[str] = None, **kwargs):
        super().__init__(message, tool_name, error_code="ValidationError", **kwargs)
        self.validation_errors = validation_errors or []


class ToolNotFoundError(ToolError):
    """Raised when a requested tool is not registered."""

    def __init__(self, tool_name: str = "", **kwargs):
        message = f"Tool not found: {tool_name}" if tool_name else "Tool not found"
        super().__init__(message, tool_name, error_code="NotFoundError", **kwargs)


class ToolDisabledError(ToolError):
    """Raised when a tool is disabled."""

    def __init__(self, tool_name: str = "", reason: str = "", **kwargs):
        message = f"Tool disabled: {tool_name}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, tool_name, error_code="DisabledError", **kwargs)
        self.reason = reason


class ToolExecutionError(ToolError):
    """Raised when a tool fails during execution."""

    def __init__(self, message: str = "Tool execution failed",
                 tool_name: str = "", original_error: str = "", **kwargs):
        super().__init__(message, tool_name, error_code="ExecutionError", **kwargs)
        self.original_error = original_error


class ToolApprovalError(ToolError):
    """Raised when a tool requires approval but none was granted."""

    def __init__(self, message: str = "Approval required but not granted",
                 tool_name: str = "", request_id: str = "", **kwargs):
        super().__init__(message, tool_name, error_code="ApprovalError", **kwargs)
        self.request_id = request_id


class ToolSandboxError(ToolError):
    """Raised when sandbox execution fails."""

    def __init__(self, message: str = "Sandbox execution failed",
                 tool_name: str = "", sandbox_type: str = "", **kwargs):
        super().__init__(message, tool_name, error_code="SandboxError", **kwargs)
        self.sandbox_type = sandbox_type


class ToolRateLimitError(ToolError):
    """Raised when a tool rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded",
                 tool_name: str = "", retry_after_sec: int = 0, **kwargs):
        super().__init__(message, tool_name, error_code="RateLimitError", **kwargs)
        self.retry_after_sec = retry_after_sec


class ToolDependencyError(ToolError):
    """Raised when a tool dependency is missing."""

    def __init__(self, message: str = "Missing dependency",
                 tool_name: str = "", dependency: str = "", **kwargs):
        super().__init__(message, tool_name, error_code="DependencyError", **kwargs)
        self.dependency = dependency
