"""ASTRA TUI Application — Mission Control Dashboard"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class DashboardConfig:
    refresh_interval: int = 5
    theme: str = "dark"
    show_audit: bool = True
    show_memory: bool = True
    show_tools: bool = True


class AstraDashboard:
    """Terminal UI Dashboard for ASTRA Command OS."""

    def __init__(self, config: DashboardConfig = None):
        self.config = config or DashboardConfig()
        self.sections = {}

    def render_header(self, mission_goal: str, progress: float) -> str:
        bar_len = 40
        filled = int(progress / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        return f"""
┌────────────────────────────────────────────────────────────┐
│ ASTRA COMMAND — {mission_goal[:45]:<45} │
│ Progress: [{bar}] {progress:.1f}%{'':<5}│
└────────────────────────────────────────────────────────────┘"""

    def render_stats(self, stats: dict) -> str:
        return f"""
┌─ System ──────────────┬─ Tasks ──────────────┐
│ Missions: {stats.get('missions', 0):<12}│ Total: {stats.get('total_tasks', 0):<13}│
│ Active:   {stats.get('active', 0):<12}│ Done:  {stats.get('done_tasks', 0):<13}│
│ Memory:   {stats.get('memories', 0):<12}│ Failed:{stats.get('failed', 0):<13}│
└───────────────────────┴──────────────────────┘"""

    def render_recent(self, items: list[dict], title: str = "Recent") -> str:
        lines = [f"┌─ {title} ─{'─' * (50 - len(title))}┐"]
        for item in items[:5]:
            name = item.get("name", "?")[:30]
            status = item.get("status", "?")
            lines.append(f"│ {name:<35} {status:<13} │")
        lines.append(f"└{'─' * 52}┘")
        return "\n".join(lines)

    def render_full(self, mission_goal: str, progress: float, stats: dict,
                    recent_missions: list[dict], recent_tools: list[dict]) -> str:
        parts = [
            self.render_header(mission_goal, progress),
            self.render_stats(stats),
            self.render_recent(recent_missions, "Missions"),
            self.render_recent(recent_tools, "Tool Calls"),
        ]
        return "\n".join(parts)
