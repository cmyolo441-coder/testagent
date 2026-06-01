"""Tool Stream Screen — Live tool execution stream"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ToolExecution:
    id: str = ""
    tool_name: str = ""
    status: str = "queued"  # queued, running, completed, failed, timeout
    parameters: dict = field(default_factory=dict)
    result: Optional[str] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    agent_id: Optional[str] = None
    mission_id: Optional[str] = None
    tokens_used: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


@dataclass
class ToolRegistry:
    name: str = ""
    description: str = ""
    category: str = ""
    permission_level: str = "standard"
    avg_duration_ms: float = 0.0
    success_rate: float = 1.0
    total_executions: int = 0


class ToolStreamScreen:
    """Live tool execution stream screen."""

    TITLE = "Tool Stream"

    def __init__(self):
        self.executions: list[ToolExecution] = []
        self.registry: dict[str, ToolRegistry] = {}
        self.stream_buffer: list[str] = []
        self.max_buffer: int = 100
        self.is_streaming: bool = True
        self.filter_tool: str = ""
        self.filter_status: str = ""

    def register_tool(self, name: str, description: str = "",
                      category: str = "general",
                      permission_level: str = "standard") -> ToolRegistry:
        tool = ToolRegistry(
            name=name,
            description=description,
            category=category,
            permission_level=permission_level,
        )
        self.registry[name] = tool
        return tool

    def start_execution(self, tool_name: str, parameters: dict = None,
                        agent_id: str = None, mission_id: str = None) -> ToolExecution:
        exec_id = f"TOOL-{len(self.executions) + 1:06d}"
        execution = ToolExecution(
            id=exec_id,
            tool_name=tool_name,
            parameters=parameters or {},
            agent_id=agent_id,
            mission_id=mission_id,
            status="running",
        )
        self.executions.append(execution)
        self._add_to_stream(f"▶ {tool_name} started ({exec_id})")
        return execution

    def complete_execution(self, execution_id: str, result: str = "",
                           duration_ms: float = 0.0, tokens_used: int = 0) -> Optional[ToolExecution]:
        for exec in self.executions:
            if exec.id == execution_id:
                exec.status = "completed"
                exec.result = result
                exec.duration_ms = duration_ms
                exec.tokens_used = tokens_used
                exec.completed_at = datetime.now(timezone.utc).isoformat()
                self._update_tool_stats(exec.tool_name, True, duration_ms)
                self._add_to_stream(f"✓ {exec.tool_name} completed in {duration_ms:.0f}ms")
                return exec
        return None

    def fail_execution(self, execution_id: str, error: str = "",
                       duration_ms: float = 0.0) -> Optional[ToolExecution]:
        for exec in self.executions:
            if exec.id == execution_id:
                exec.status = "failed"
                exec.error = error
                exec.duration_ms = duration_ms
                exec.completed_at = datetime.now(timezone.utc).isoformat()
                self._update_tool_stats(exec.tool_name, False, duration_ms)
                self._add_to_stream(f"✗ {exec.tool_name} failed: {error[:50]}")
                return exec
        return None

    def _update_tool_stats(self, tool_name: str, success: bool, duration_ms: float):
        tool = self.registry.get(tool_name)
        if not tool:
            return
        tool.total_executions += 1
        n = tool.total_executions
        tool.avg_duration_ms = ((tool.avg_duration_ms * (n - 1)) + duration_ms) / n
        if success:
            tool.success_rate = ((tool.success_rate * (n - 1)) + 1.0) / n
        else:
            tool.success_rate = ((tool.success_rate * (n - 1)) + 0.0) / n

    def _add_to_stream(self, message: str):
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.stream_buffer.append(f"[{timestamp}] {message}")
        if len(self.stream_buffer) > self.max_buffer:
            self.stream_buffer = self.stream_buffer[-self.max_buffer:]

    def get_recent_executions(self, limit: int = 20) -> list[ToolExecution]:
        return self.executions[-limit:]

    def get_running_executions(self) -> list[ToolExecution]:
        return [e for e in self.executions if e.status == "running"]

    def get_failed_executions(self, limit: int = 10) -> list[ToolExecution]:
        failed = [e for e in self.executions if e.status == "failed"]
        return failed[-limit:]

    def get_tool_stats(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "executions": t.total_executions,
                "success_rate": t.success_rate,
                "avg_duration": t.avg_duration_ms,
            }
            for t in sorted(self.registry.values(), key=lambda x: x.total_executions, reverse=True)
        ]

    def get_total_tokens(self) -> int:
        return sum(e.tokens_used for e in self.executions)

    def get_total_duration(self) -> float:
        return sum(e.duration_ms for e in self.executions)

    def render_header(self) -> str:
        total = len(self.executions)
        running = len(self.get_running_executions())
        failed = sum(1 for e in self.executions if e.status == "failed")
        return f"╔══════════════════════════════════════════════════════════╗\n║ TOOL STREAM — {total} executions ({running} running, {failed} failed){'':<8}║\n║ Tokens used: {self.get_total_tokens():<43}║\n╚══════════════════════════════════════════════════════════╝"

    def render_live_stream(self) -> str:
        lines = ["┌─ Live Stream ───────────────────────────────────────┐"]
        for msg in self.stream_buffer[-8:]:
            lines.append(f"│ {msg[:52]:<52} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_tool_stats(self) -> str:
        lines = ["┌─ Tool Statistics ───────────────────────────────────┐"]
        for stat in self.get_tool_stats()[:5]:
            rate = f"{stat['success_rate']:.0%}"
            lines.append(f"│ {stat['name'][:18]:<18} {stat['executions']:>5} exec {rate:>5} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_full(self) -> str:
        parts = [
            self.render_header(),
            "",
            self.render_live_stream(),
            "",
            self.render_tool_stats(),
        ]
        return "\n".join(parts)

    def get_stats(self) -> dict:
        executions = self.executions
        return {
            "total_executions": len(executions),
            "running": len(self.get_running_executions()),
            "completed": sum(1 for e in executions if e.status == "completed"),
            "failed": sum(1 for e in executions if e.status == "failed"),
            "registered_tools": len(self.registry),
            "total_tokens": self.get_total_tokens(),
        }
