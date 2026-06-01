"""Live Logs Widget — Real-time log stream display"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class LogEntry:
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    source: str = ""
    message: str = ""
    metadata: dict = field(default_factory=dict)


class LiveLogs:
    """Real-time log stream widget."""

    LEVEL_COLORS = {
        "DEBUG": "#666680",
        "INFO": "#00D4FF",
        "WARNING": "#FFB800",
        "ERROR": "#FF4444",
        "CRITICAL": "#FF0000",
    }

    LEVEL_ICONS = {
        "DEBUG": "D",
        "INFO": "I",
        "WARNING": "W",
        "ERROR": "E",
        "CRITICAL": "C",
    }

    def __init__(self, max_entries: int = 200, max_display: int = 15):
        self.max_entries = max_entries
        self.max_display = max_display
        self.entries: list[LogEntry] = []
        self.filter_level: str = ""
        self.filter_source: str = ""
        self.filter_text: str = ""
        self.auto_scroll: bool = True
        self.is_paused: bool = False
        self.scroll_offset: int = 0

    def log(self, level: str, message: str, source: str = "",
            metadata: dict = None) -> LogEntry:
        entry = LogEntry(
            level=level.upper(),
            source=source,
            message=message,
            metadata=metadata or {},
        )
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
        return entry

    def debug(self, message: str, source: str = "") -> LogEntry:
        return self.log("DEBUG", message, source)

    def info(self, message: str, source: str = "") -> LogEntry:
        return self.log("INFO", message, source)

    def warning(self, message: str, source: str = "") -> LogEntry:
        return self.log("WARNING", message, source)

    def error(self, message: str, source: str = "") -> LogEntry:
        return self.log("ERROR", message, source)

    def critical(self, message: str, source: str = "") -> LogEntry:
        return self.log("CRITICAL", message, source)

    def get_filtered(self) -> list[LogEntry]:
        results = list(self.entries)
        if self.filter_level:
            results = [e for e in results if e.level == self.filter_level.upper()]
        if self.filter_source:
            results = [e for e in results if self.filter_source.lower() in e.source.lower()]
        if self.filter_text:
            results = [e for e in results if self.filter_text.lower() in e.message.lower()]
        return results

    def get_visible(self) -> list[LogEntry]:
        filtered = self.get_filtered()
        if self.auto_scroll and not self.is_paused:
            return filtered[-self.max_display:]
        start = max(0, len(filtered) - self.max_display - self.scroll_offset)
        end = len(filtered) - self.scroll_offset if self.scroll_offset > 0 else len(filtered)
        return filtered[start:end]

    def scroll_up(self, lines: int = 5):
        self.scroll_offset += lines
        if self.scroll_offset > len(self.entries) - self.max_display:
            self.scroll_offset = max(0, len(self.entries) - self.max_display)

    def scroll_down(self, lines: int = 5):
        self.scroll_offset = max(0, self.scroll_offset - lines)

    def scroll_to_bottom(self):
        self.scroll_offset = 0
        self.auto_scroll = True

    def pause(self):
        self.is_paused = True
        self.auto_scroll = False

    def resume(self):
        self.is_paused = False
        self.auto_scroll = True
        self.scroll_offset = 0

    def clear(self):
        self.entries.clear()
        self.scroll_offset = 0

    def render_entry(self, entry: LogEntry) -> str:
        icon = self.LEVEL_ICONS.get(entry.level, "?")
        ts = entry.timestamp[11:19] if len(entry.timestamp) > 19 else entry.timestamp[:8]
        source = f"[{entry.source}]" if entry.source else ""
        return f" {ts} {icon} {source:<12} {entry.message[:48]}"

    def render(self) -> str:
        visible = self.get_visible()
        lines = ["┌─ Live Logs ─────────────────────────────────────────┐"]
        for entry in visible:
            lines.append(f"│{self.render_entry(entry)}│")
        if not visible:
            lines.append(f"│ {'No log entries':<52} │")
        status = "▶ RUNNING" if not self.is_paused else "║ PAUSED"
        lines.append(f"└─ {status} {'─' * (47 - len(status))}┘")
        return "\n".join(lines)

    def render_header(self) -> str:
        total = len(self.entries)
        filtered = len(self.get_filtered())
        return f"Logs: {total} total, {filtered} shown | Filter: {self.filter_level or 'all'}"

    def get_stats(self) -> dict:
        entries = self.entries
        by_level = {}
        for e in entries:
            by_level[e.level] = by_level.get(e.level, 0) + 1
        return {
            "total_entries": len(entries),
            "by_level": by_level,
            "is_paused": self.is_paused,
            "filter_active": bool(self.filter_level or self.filter_source or self.filter_text),
        }
