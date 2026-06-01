"""Audit Replay Screen — Audit trail replay and investigation"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class AuditEntry:
    id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: str = ""  # command, tool_call, decision, approval, error, system
    actor: str = ""  # agent_id, user_id, system
    action: str = ""
    target: str = ""
    result: str = ""
    details: dict = field(default_factory=dict)
    risk_level: str = "low"
    reversible: bool = True
    session_id: Optional[str] = None
    mission_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)


@dataclass
class AuditFilter:
    event_type: str = ""
    actor: str = ""
    risk_level: str = ""
    start_time: str = ""
    end_time: str = ""
    tags: list[str] = field(default_factory=list)
    search_query: str = ""


class AuditReplayScreen:
    """Audit trail replay and investigation screen."""

    TITLE = "Audit Replay"

    def __init__(self):
        self.entries: list[AuditEntry] = []
        self.filters: AuditFilter = AuditFilter()
        self.replay_position: int = 0
        self.replay_speed: float = 1.0
        self.is_replaying: bool = False
        self.bookmarks: list[int] = []

    def log_event(self, event_type: str, actor: str, action: str,
                  target: str = "", result: str = "", details: dict = None,
                  risk_level: str = "low", reversible: bool = True,
                  session_id: str = None, mission_id: str = None,
                  tags: list[str] = None) -> AuditEntry:
        entry = AuditEntry(
            event_type=event_type,
            actor=actor,
            action=action,
            target=target,
            result=result,
            details=details or {},
            risk_level=risk_level,
            reversible=reversible,
            session_id=session_id,
            mission_id=mission_id,
            tags=tags or [],
        )
        self.entries.append(entry)
        return entry

    def get_filtered_entries(self, audit_filter: AuditFilter = None) -> list[AuditEntry]:
        f = audit_filter or self.filters
        results = list(self.entries)
        if f.event_type:
            results = [e for e in results if e.event_type == f.event_type]
        if f.actor:
            results = [e for e in results if e.actor == f.actor]
        if f.risk_level:
            results = [e for e in results if e.risk_level == f.risk_level]
        if f.start_time:
            results = [e for e in results if e.timestamp >= f.start_time]
        if f.end_time:
            results = [e for e in results if e.timestamp <= f.end_time]
        if f.tags:
            tag_set = set(f.tags)
            results = [e for e in results if tag_set & set(e.tags)]
        if f.search_query:
            q = f.search_query.lower()
            results = [e for e in results if q in e.action.lower() or q in e.target.lower()]
        return results

    def start_replay(self, start_position: int = 0):
        self.replay_position = start_position
        self.is_replaying = True

    def step_forward(self) -> Optional[AuditEntry]:
        if self.replay_position < len(self.entries):
            entry = self.entries[self.replay_position]
            self.replay_position += 1
            return entry
        self.is_replaying = False
        return None

    def step_backward(self) -> Optional[AuditEntry]:
        if self.replay_position > 0:
            self.replay_position -= 1
            return self.entries[self.replay_position]
        return None

    def jump_to(self, position: int) -> Optional[AuditEntry]:
        if 0 <= position < len(self.entries):
            self.replay_position = position
            return self.entries[position]
        return None

    def add_bookmark(self, position: int = None):
        pos = position if position is not None else self.replay_position
        if pos not in self.bookmarks:
            self.bookmarks.append(pos)
            self.bookmarks.sort()

    def remove_bookmark(self, position: int):
        if position in self.bookmarks:
            self.bookmarks.remove(position)

    def get_entry_by_id(self, entry_id: str) -> Optional[AuditEntry]:
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None

    def get_entries_by_actor(self, actor: str) -> list[AuditEntry]:
        return [e for e in self.entries if e.actor == actor]

    def get_entries_by_type(self, event_type: str) -> list[AuditEntry]:
        return [e for e in self.entries if e.event_type == event_type]

    def get_high_risk_entries(self) -> list[AuditEntry]:
        return [e for e in self.entries if e.risk_level in ("high", "critical")]

    def get_irreversible_actions(self) -> list[AuditEntry]:
        return [e for e in self.entries if not e.reversible]

    def get_timeline_summary(self) -> dict:
        if not self.entries:
            return {"total": 0}
        by_type = {}
        by_actor = {}
        by_risk = {}
        for e in self.entries:
            by_type[e.event_type] = by_type.get(e.event_type, 0) + 1
            by_actor[e.actor] = by_actor.get(e.actor, 0) + 1
            by_risk[e.risk_level] = by_risk.get(e.risk_level, 0) + 1
        return {
            "total": len(self.entries),
            "by_type": by_type,
            "by_actor": by_actor,
            "by_risk": by_risk,
            "start_time": self.entries[0].timestamp,
            "end_time": self.entries[-1].timestamp,
        }

    def render_header(self) -> str:
        total = len(self.entries)
        high_risk = len(self.get_high_risk_entries())
        position = self.replay_position
        return f"╔══════════════════════════════════════════════════════════╗\n║ AUDIT REPLAY — {total} entries ({high_risk} high-risk){'':<17}║\n║ Position: {position}/{total}{'':<39}║\n╚══════════════════════════════════════════════════════════╝"

    def render_timeline(self) -> str:
        lines = ["┌─ Audit Timeline ────────────────────────────────────┐"]
        start = max(0, self.replay_position - 3)
        end = min(len(self.entries), self.replay_position + 5)
        for i in range(start, end):
            entry = self.entries[i]
            marker = ">>>" if i == self.replay_position else "   "
            risk_icon = {"critical": "!", "high": "H", "medium": "M", "low": "L"}.get(entry.risk_level, "?")
            lines.append(f"│ {marker} [{risk_icon}] {entry.timestamp[:16]} {entry.action[:28]:<28} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_current_entry(self) -> str:
        if self.replay_position >= len(self.entries):
            return "  No entry at current position"
        entry = self.entries[self.replay_position]
        lines = [
            "┌─ Current Entry ────────────────────────────────────┐",
            f"│ ID:       {entry.id:<40} │",
            f"│ Time:     {entry.timestamp[:40]:<40} │",
            f"│ Type:     {entry.event_type:<40} │",
            f"│ Actor:    {entry.actor:<40} │",
            f"│ Action:   {entry.action[:40]:<40} │",
            f"│ Target:   {entry.target[:40]:<40} │",
            f"│ Result:   {entry.result[:40]:<40} │",
            f"│ Risk:     {entry.risk_level:<40} │",
            "└────────────────────────────────────────────────────┘",
        ]
        return "\n".join(lines)

    def render_full(self) -> str:
        parts = [
            self.render_header(),
            "",
            self.render_timeline(),
            "",
            self.render_current_entry(),
        ]
        return "\n".join(parts)

    def get_stats(self) -> dict:
        entries = self.entries
        return {
            "total_entries": len(entries),
            "high_risk": len(self.get_high_risk_entries()),
            "irreversible": len(self.get_irreversible_actions()),
            "bookmarks": len(self.bookmarks),
            "replay_position": self.replay_position,
        }
