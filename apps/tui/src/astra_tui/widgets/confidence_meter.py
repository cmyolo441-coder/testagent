"""Confidence Meter Widget — Visual confidence display"""
from dataclasses import dataclass


@dataclass
class ConfidenceLevel:
    label: str
    min_value: float
    max_value: float
    color: str
    description: str


class ConfidenceMeter:
    """Visual confidence meter with configurable levels."""

    DEFAULT_LEVELS = [
        ConfidenceLevel("Very High", 0.9, 1.0, "#00FF88", "Near certain"),
        ConfidenceLevel("High", 0.75, 0.9, "#00D4FF", "Very likely"),
        ConfidenceLevel("Medium", 0.5, 0.75, "#FFB800", "Likely"),
        ConfidenceLevel("Low", 0.25, 0.5, "#FF6B9D", "Uncertain"),
        ConfidenceLevel("Very Low", 0.0, 0.25, "#FF4444", "Very uncertain"),
    ]

    def __init__(self, value: float = 0.5, label: str = "",
                 levels: list[ConfidenceLevel] = None):
        self.value = max(0.0, min(1.0, value))
        self.label = label
        self.levels = levels or self.DEFAULT_LEVELS
        self.history: list[float] = [self.value]

    def set_value(self, value: float):
        self.value = max(0.0, min(1.0, value))
        self.history.append(self.value)

    def get_level(self) -> ConfidenceLevel:
        for level in self.levels:
            if level.min_value <= self.value < level.max_value:
                return level
        return self.levels[-1]

    def get_color(self) -> str:
        return self.get_level().color

    def get_description(self) -> str:
        return self.get_level().description

    def get_trend(self) -> str:
        if len(self.history) < 2:
            return "stable"
        recent = self.history[-3:] if len(self.history) >= 3 else self.history
        if recent[-1] > recent[0]:
            return "increasing"
        elif recent[-1] < recent[0]:
            return "decreasing"
        return "stable"

    def render_bar(self, width: int = 30) -> str:
        filled = int(self.value * width)
        empty = width - filled
        bar = "█" * filled + "░" * empty
        return f"[{bar}] {self.value:.1%}"

    def render_compact(self) -> str:
        level = self.get_level()
        trend = self.get_trend()
        trend_icon = {"increasing": "↑", "decreasing": "↓", "stable": "→"}[trend]
        return f"{self.label}: {self.value:.1%} {trend_icon} ({level.label})"

    def render_full(self) -> str:
        level = self.get_level()
        lines = [
            f"┌─ Confidence: {self.label} ─{'─' * (30 - len(self.label))}┐",
            f"│ {self.render_bar(30):<42} │",
            f"│ Level: {level.label:<34} │",
            f"│ {level.description:<42} │",
            f"│ Trend: {self.get_trend():<34} │",
            f"│ History: {' → '.join(f'{v:.0%}' for v in self.history[-5:]):<34} │",
            f"└{'─' * 44}┘",
        ]
        return "\n".join(lines)

    def render_gauge(self) -> str:
        gauge_width = 20
        filled = int(self.value * gauge_width)
        segments = []
        for i in range(gauge_width):
            if i < filled:
                segments.append("━")
            else:
                segments.append("─")
        gauge = "".join(segments)
        return f" {self.value:.0%} ┃{gauge}┃"

    def get_stats(self) -> dict:
        return {
            "value": self.value,
            "level": self.get_level().label,
            "trend": self.get_trend(),
            "history_length": len(self.history),
            "min_history": min(self.history) if self.history else 0,
            "max_history": max(self.history) if self.history else 0,
        }
