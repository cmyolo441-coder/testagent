"""Mission Control Screen — Mission timeline and progress tracking"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Mission:
    id: str = ""
    name: str = ""
    description: str = ""
    status: str = "planning"  # planning, active, paused, completed, failed
    progress: float = 0.0
    objectives: list[str] = field(default_factory=list)
    completed_objectives: list[str] = field(default_factory=list)
    agents_assigned: list[str] = field(default_factory=list)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    deadline: Optional[str] = None
    priority: str = "medium"
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class MissionEvent:
    mission_id: str
    event_type: str = ""  # started, milestone, blocked, completed, failed
    description: str = ""
    agent_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MissionControlScreen:
    """Mission timeline and progress screen."""

    TITLE = "Mission Control"

    def __init__(self):
        self.missions: dict[str, Mission] = {}
        self.events: list[MissionEvent] = []
        self.active_mission_id: Optional[str] = None

    def create_mission(self, name: str, description: str = "",
                       objectives: list[str] = None, priority: str = "medium",
                       deadline: str = None, tags: list[str] = None) -> Mission:
        mission_id = f"MSN-{len(self.missions) + 1:04d}"
        mission = Mission(
            id=mission_id,
            name=name,
            description=description,
            objectives=objectives or [],
            priority=priority,
            deadline=deadline,
            tags=tags or [],
            start_time=datetime.now(timezone.utc).isoformat(),
        )
        self.missions[mission_id] = mission
        self._add_event(mission_id, "created", f"Mission '{name}' created")
        return mission

    def update_mission(self, mission_id: str, progress: float = None,
                       status: str = None) -> Optional[Mission]:
        mission = self.missions.get(mission_id)
        if not mission:
            return None
        if progress is not None:
            mission.progress = min(100.0, max(0.0, progress))
        if status:
            mission.status = status
            self._add_event(mission_id, status, f"Mission status changed to {status}")
        return mission

    def complete_objective(self, mission_id: str, objective: str) -> bool:
        mission = self.missions.get(mission_id)
        if not mission or objective not in mission.objectives:
            return False
        if objective not in mission.completed_objectives:
            mission.completed_objectives.append(objective)
            total = len(mission.objectives)
            done = len(mission.completed_objectives)
            mission.progress = (done / total) * 100 if total > 0 else 0
            self._add_event(mission_id, "milestone", f"Objective completed: {objective}")
            if done == total:
                mission.status = "completed"
                mission.end_time = datetime.now(timezone.utc).isoformat()
                self._add_event(mission_id, "completed", "All objectives completed")
        return True

    def get_active_missions(self) -> list[Mission]:
        return [m for m in self.missions.values() if m.status == "active"]

    def get_mission_timeline(self, mission_id: str) -> list[MissionEvent]:
        return [e for e in self.events if e.mission_id == mission_id]

    def get_overall_progress(self) -> float:
        missions = list(self.missions.values())
        if not missions:
            return 0.0
        return sum(m.progress for m in missions) / len(missions)

    def render_header(self) -> str:
        active = len(self.get_active_missions())
        total = len(self.missions)
        overall = self.get_overall_progress()
        bar_len = 40
        filled = int(overall / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        return f"╔══════════════════════════════════════════════════════════╗\n║ MISSION CONTROL — {active} active / {total} total{'':<18}║\n║ Overall: [{bar}] {overall:.1f}%{'':<14}║\n╚══════════════════════════════════════════════════════════╝"

    def render_mission_list(self) -> str:
        lines = ["┌─ Active Missions ──────────────────────────────────┐"]
        for mission in self.get_active_missions()[:5]:
            bar_len = 20
            filled = int(mission.progress / 100 * bar_len)
            bar = "█" * filled + "░" * (bar_len - filled)
            lines.append(f"│ {mission.name[:25]:<25} [{bar}] {mission.progress:.0f}% │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_recent_events(self) -> str:
        lines = ["┌─ Recent Events ────────────────────────────────────┐"]
        for event in self.events[-5:]:
            lines.append(f"│ {event.timestamp[:16]} {event.event_type:<12} {event.description[:28]:<28} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_full(self) -> str:
        parts = [
            self.render_header(),
            "",
            self.render_mission_list(),
            "",
            self.render_recent_events(),
        ]
        return "\n".join(parts)

    def _add_event(self, mission_id: str, event_type: str, description: str):
        event = MissionEvent(
            mission_id=mission_id,
            event_type=event_type,
            description=description,
        )
        self.events.append(event)

    def get_stats(self) -> dict:
        missions = list(self.missions.values())
        return {
            "total_missions": len(missions),
            "active": len([m for m in missions if m.status == "active"]),
            "completed": len([m for m in missions if m.status == "completed"]),
            "failed": len([m for m in missions if m.status == "failed"]),
            "total_events": len(self.events),
        }
