"""Agent Runtime — Main agent execution environment"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Any
from datetime import datetime, timezone
import uuid
import json


class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING_APPROVAL = "waiting_approval"
    WAITING_INPUT = "waiting_input"
    ERROR = "error"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class AgentConfig:
    agent_id: str = field(default_factory=lambda: f"AGENT-{uuid.uuid4().hex[:8]}")
    name: str = "ASTRA Agent"
    role: str = "general"
    model: str = "default"
    max_iterations: int = 50
    max_tokens_per_step: int = 4096
    temperature: float = 0.7
    tools: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    safety_level: str = "standard"  # strict, standard, relaxed
    memory_enabled: bool = True
    verification_enabled: bool = True


@dataclass
class AgentState:
    status: AgentStatus = AgentStatus.IDLE
    current_mission_id: Optional[str] = None
    current_task_id: Optional[str] = None
    iteration: int = 0
    total_tokens_used: int = 0
    total_tool_calls: int = 0
    errors: list[dict] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_active: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ToolCall:
    id: str = field(default_factory=lambda: f"TC-{uuid.uuid4().hex[:8]}")
    tool_name: str = ""
    arguments: dict = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    duration_ms: float = 0
    risk_score: int = 0
    approved: bool = True
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentRuntime:
    """Main runtime for agent execution."""

    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.state = AgentState()
        self.tools: dict[str, Callable] = {}
        self.tool_history: list[ToolCall] = []
        self.event_handlers: dict[str, list[Callable]] = {}

    def register_tool(self, name: str, handler: Callable):
        self.tools[name] = handler

    def on(self, event: str, handler: Callable):
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)

    def emit(self, event: str, data: dict = None):
        for handler in self.event_handlers.get(event, []):
            handler(data or {})

    def execute_tool(self, tool_name: str, arguments: dict) -> ToolCall:
        tool_call = ToolCall(tool_name=tool_name, arguments=arguments)

        if tool_name not in self.tools:
            tool_call.error = f"Unknown tool: {tool_name}"
            return tool_call

        try:
            start = datetime.now(timezone.utc)
            result = self.tools[tool_name](**arguments)
            end = datetime.now(timezone.utc)
            tool_call.result = result
            tool_call.duration_ms = (end - start).total_seconds() * 1000
        except Exception as e:
            tool_call.error = str(e)

        self.tool_history.append(tool_call)
        self.state.total_tool_calls += 1
        self.emit("tool_call", {"tool": tool_name, "success": tool_call.error is None})
        return tool_call

    def get_context_summary(self) -> dict:
        return {
            "agent_id": self.config.agent_id,
            "status": self.state.status.value,
            "mission_id": self.state.current_mission_id,
            "task_id": self.state.current_task_id,
            "iteration": self.state.iteration,
            "tokens_used": self.state.total_tokens_used,
            "tool_calls": self.state.total_tool_calls,
            "errors": len(self.state.errors),
        }

    def to_dict(self) -> dict:
        return {
            "config": {
                "agent_id": self.config.agent_id,
                "name": self.config.name,
                "role": self.config.role,
                "model": self.config.model,
                "tools": self.config.tools,
            },
            "state": {
                "status": self.state.status.value,
                "iteration": self.state.iteration,
                "total_tokens": self.state.total_tokens_used,
                "total_tool_calls": self.state.total_tool_calls,
            },
            "tool_history_count": len(self.tool_history),
        }
