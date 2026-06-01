"""Mission Timeline Widget — Visual timeline of mission progress"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class TimelineEvent:
    id: str = ""
    mission_id: str = ""
    title: str = ""
    description: str = ""
    event_type: str = ""  # started, milestone, blocked, completed, failed
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_ms: float = 0.0
    metadata: dict = field(default_factory=dict)


class MissionTimeline:
    """Visual timeline widget for mission events."""

    def __init__(self, mission_id: str = "", max_events: int = 50):
        self.mission_id = mission_id
        self.max_events = max_events
        self.events: list[TimelineEvent] = []
        self.view_mode: str = "compact"  # compact, detailed, minimal

    def add_event(self, title: str, event_type: str = "milestone",
                  description: str = "", duration_ms: float = 0.0,
                  metadata: dict = None) -> TimelineEvent:
        event = TimelineEvent(
            id=f"TE-{len(self.events) + 1:04d}",
            mission_id=self.mission_id,
            title=title,
            description=description,
            event_type=event_type,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
        return event

    def get_events_in_range(self, start: str, end: str) -> list[TimelineEvent]:
        return [e for e in self.events if start <= e.timestamp <= end]

    def get_events_by_type(self, event_type: str) -> list[TimelineEvent]:
        return [e for e in self.events if e.event_type == event_type]

    def get_progress_percentage(self) -> float:
        if not self.events:
            return 0.0
        completed = sum(1 for e in self.events if e.event_type == "completed")
        total = len(self.events)
        return (completed / total) * 100 if total > 0 else 0.0

    def get_duration_summary(self) -> dict:
        total_ms = sum(e.duration_ms for e in self.events)
        by_type = {}
        for e in self.events:
            by_type[e.event_type] = by_type.get(e.event_type, 0) + e.duration_ms
        return {
            "total_ms": total_ms,
            "total_hours": total_ms / 3600000,
            "by_type": by_type,
        }

    def render_compact(self) -> str:
        type_icons = {
            "started": "▶", "milestone": "◆", "blocked": "▼",
            "completed": "●", "failed": "✗", "paused": "║",
        }
        lines = ["┌─ Mission Timeline ──────────────────────────────────┐"]
        for event in self.events[-8:]:
            icon = type_icons.get(event.event_type, "○")
            ts = event.timestamp[:16] if event.timestamp else "?"
            lines.append(f"│ {icon} {ts} {event.title[:30]:<30} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_detailed(self) -> str:
        lines = ["┌─ Mission Timeline (Detailed) ───────────────────────┐"]
        for event in self.events[-6:]:
            lines.append(f"│ {event.timestamp[:19]} [{event.event_type}]{'':<16} │")
            lines.append(f"│   {event.title:<50} │")
            if event.description:
                lines.append(f"│   {event.description[:50]:<50} │")
            lines.append(f"│{'':<54}│")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_minimal(self) -> str:
        if not self.events:
            return "  No timeline events"
        last = self.events[-1]
        return f"  Last: {last.title} ({last.event_type}) at {last.timestamp[:16]}"

    def render(self) -> str:
        if self.view_mode == "detailed":
            return self.render_detailed()
        elif self.view_mode == "minimal":
            return self.render_minimal()
        return self.render_compact()

    def get_stats(self) -> dict:
        return {
            "total_events": len(self.events),
            "event_types": {e.event_type: sum(1 for ev in self.events if ev.event_type == e.event_type)
                           for e in self.events},
            "progress": self.get_progress_percentage(),
            "duration": self.get_duration_summary(),
        }
