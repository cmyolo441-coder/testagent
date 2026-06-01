"""ASTRA TUI Theme — Color scheme and styling constants"""
from dataclasses import dataclass, field


@dataclass
class ColorPalette:
    primary: str = "#00D4FF"
    secondary: str = "#7B68EE"
    accent: str = "#FF6B9D"
    success: str = "#00FF88"
    warning: str = "#FFB800"
    danger: str = "#FF4444"
    info: str = "#44AAFF"
    muted: str = "#666680"
    background: str = "#0A0E1A"
    surface: str = "#12162A"
    surface_light: str = "#1A1F35"
    text: str = "#E0E0F0"
    text_dim: str = "#888899"
    border: str = "#2A2F45"
    highlight: str = "#1E2A4A"


@dataclass
class AstraTheme:
    name: str = "nebula"
    colors: ColorPalette = field(default_factory=ColorPalette)
    font_family: str = "monospace"
    border_style: str = "round"
    show_borders: bool = True
    compact_mode: bool = False

    STATUS_COLORS: dict = field(default_factory=lambda: {
        "active": "#00FF88",
        "completed": "#00D4FF",
        "pending": "#FFB800",
        "failed": "#FF4444",
        "paused": "#666680",
        "in_progress": "#7B68EE",
        "blocked": "#FF6B9D",
    })

    SEVERITY_COLORS: dict = field(default_factory=lambda: {
        "critical": "#FF4444",
        "high": "#FF6B9D",
        "medium": "#FFB800",
        "low": "#00D4FF",
        "info": "#44AAFF",
    })

    AGENT_ROLE_COLORS: dict = field(default_factory=lambda: {
        "planner": "#7B68EE",
        "executor": "#00FF88",
        "reviewer": "#FFB800",
        "researcher": "#44AAFF",
        "architect": "#FF6B9D",
    })

    def get_status_color(self, status: str) -> str:
        return self.STATUS_COLORS.get(status, self.colors.muted)

    def get_severity_color(self, severity: str) -> str:
        return self.SEVERITY_COLORS.get(severity, self.colors.muted)

    def get_agent_color(self, role: str) -> str:
        return self.AGENT_ROLE_COLORS.get(role, self.colors.primary)

    def render_box(self, title: str, content: str, width: int = 60) -> str:
        border = "─" * (width - 2)
        lines = content.split("\n")
        padded = [f"│ {line:<{width - 4}} │" for line in lines]
        return f"┌─ {title} {border[len(title) + 1:]}┐\n" + "\n".join(padded) + f"\n└{'─' * (width - 2)}┘"

    def render_progress(self, label: str, progress: float, width: int = 30) -> str:
        filled = int(progress / 100 * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"{label}: [{bar}] {progress:.1f}%"

    def render_table(self, headers: list[str], rows: list[list[str]], widths: list[int] = None) -> str:
        if not widths:
            widths = [max(len(h), max((len(r[i]) for r in rows), default=0)) + 2
                      for i, h in enumerate(headers)]

        header_line = "│".join(f" {h:<{widths[i] - 1}}" for i, h in enumerate(headers))
        separator = "┼".join("─" * w for w in widths)
        data_lines = [
            "│".join(f" {row[i]:<{widths[i] - 1}}" for i in range(len(headers)))
            for row in rows
        ]
        return f"┌{'┬'.join('─' * w for w in widths)}┐\n{header_line}\n{separator}\n" + "\n".join(data_lines) + f"\n└{'┴'.join('─' * w for w in widths)}┘"

    def to_textual_css(self) -> str:
        return f"""
Screen {{
    background: {self.colors.background};
    color: {self.colors.text};
}}

Header {{
    background: {self.colors.surface};
    color: {self.colors.primary};
    dock: top;
}}

Footer {{
    background: {self.colors.surface};
    color: {self.colors.text_dim};
    dock: bottom;
}}

Sidebar {{
    background: {self.colors.surface};
    width: 30;
    dock: left;
}}

DataTable {{
    background: {self.colors.surface};
    color: {self.colors.text};
}}

DataTable > . datatable--header {{
    background: {self.colors.surface_light};
    color: {self.colors.primary};
    text-style: bold;
}}

Button {{
    background: {self.colors.surface_light};
    color: {self.colors.text};
    border: tall {self.colors.border};
}}

Button.-primary {{
    background: {self.colors.primary};
    color: {self.colors.background};
}}

Button.-success {{
    background: {self.colors.success};
    color: {self.colors.background};
}}

Button.-warning {{
    background: {self.colors.warning};
    color: {self.colors.background};
}}

Button.-danger {{
    background: {self.colors.danger};
    color: {self.colors.text};
}}

Input {{
    background: {self.colors.surface_light};
    color: {self.colors.text};
    border: tall {self.colors.border};
}}

Input:focus {{
    border: tall {self.colors.primary};
}}

RichLog {{
    background: {self.colors.surface};
    color: {self.colors.text};
}}
"""


THEME_DARK = AstraTheme(name="dark")
THEME_LIGHT = AstraTheme(
    name="light",
    colors=ColorPalette(
        primary="#0066CC",
        secondary="#6633CC",
        accent="#CC3366",
        success="#008844",
        warning="#CC8800",
        danger="#CC3333",
        info="#3377CC",
        muted="#888888",
        background="#FFFFFF",
        surface="#F5F5F5",
        surface_light="#EEEEEE",
        text="#1A1A2E",
        text_dim="#666666",
        border="#CCCCCC",
        highlight="#E8E8FF",
    ),
)
