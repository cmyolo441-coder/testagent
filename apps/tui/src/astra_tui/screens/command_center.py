"""Command Center Screen — Main command interface"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Command:
    id: str = ""
    name: str = ""
    description: str = ""
    command_type: str = ""  # system, agent, tool, workflow
    status: str = "pending"  # pending, running, completed, failed
    parameters: dict = field(default_factory=dict)
    result: Optional[str] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CommandCenterState:
    commands: list[Command] = field(default_factory=list)
    active_command: Optional[Command] = None
    command_history: list[Command] = field(default_factory=list)
    system_status: str = "operational"
    current_mission: Optional[str] = None
    recent_outputs: list[str] = field(default_factory=list)


class CommandCenterScreen:
    """Main command interface screen for ASTRA TUI."""

    TITLE = "Command Center"

    def __init__(self):
        self.state = CommandCenterState()
        self._command_counter = 0

    def execute_command(self, name: str, params: dict = None,
                        command_type: str = "system") -> Command:
        self._command_counter += 1
        cmd = Command(
            id=f"CMD-{self._command_counter:06d}",
            name=name,
            command_type=command_type,
            parameters=params or {},
            status="running",
        )
        self.state.active_command = cmd
        self.state.commands.append(cmd)
        return cmd

    def complete_command(self, command_id: str, result: str = "",
                         success: bool = True) -> Optional[Command]:
        for cmd in self.state.commands:
            if cmd.id == command_id:
                cmd.status = "completed" if success else "failed"
                cmd.result = result
                self.state.active_command = None
                self.state.command_history.append(cmd)
                return cmd
        return None

    def get_pending_commands(self) -> list[Command]:
        return [c for c in self.state.commands if c.status == "pending"]

    def get_recent_commands(self, limit: int = 20) -> list[Command]:
        return self.state.command_history[-limit:]

    def render_header(self) -> str:
        status_color = "●" if self.state.system_status == "operational" else "○"
        mission = self.state.current_mission or "No active mission"
        return f"╔══════════════════════════════════════════════════════════╗\n║ {status_color} ASTRA COMMAND CENTER — {mission[:30]:<30} ║\n╚══════════════════════════════════════════════════════════╝"

    def render_command_palette(self) -> str:
        lines = [
            "┌─ Commands ─────────────────────────────────────────┐",
            "│ [1] Execute Command   [2] View History             │",
            "│ [3] System Status     [4] Agent Management         │",
            "│ [5] Tool Registry     [6] Workflow Editor          │",
            "│ [7] Mission Control   [8] Memory Browser           │",
            "└────────────────────────────────────────────────────┘",
        ]
        return "\n".join(lines)

    def render_active_command(self) -> str:
        if not self.state.active_command:
            return "  No active command"
        cmd = self.state.active_command
        return f"  Active: {cmd.name} ({cmd.status})\n  ID: {cmd.id}\n  Params: {cmd.parameters}"

    def render_recent_output(self) -> str:
        lines = ["┌─ Recent Output ────────────────────────────────────┐"]
        for output in self.state.recent_outputs[-5:]:
            lines.append(f"│ {output[:52]:<52} │")
        if not self.state.recent_outputs:
            lines.append(f"│ {'No recent output':<52} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_full(self) -> str:
        parts = [
            self.render_header(),
            "",
            self.render_command_palette(),
            "",
            self.render_active_command(),
            "",
            self.render_recent_output(),
        ]
        return "\n".join(parts)

    def get_stats(self) -> dict:
        return {
            "total_commands": len(self.state.commands),
            "pending": len(self.get_pending_commands()),
            "completed": len(self.state.command_history),
            "system_status": self.state.system_status,
        }
