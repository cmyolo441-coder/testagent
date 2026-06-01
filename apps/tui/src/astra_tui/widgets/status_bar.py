"""Status Bar Widget — System status information display"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class StatusItem:
    label: str = ""
    value: str = ""
    status: str = "normal"  # normal, warning, error, success
    icon: str = ""
    tooltip: str = ""
    order: int = 0


class StatusBar:
    """System status information bar widget."""

    def __init__(self):
        self.items: list[StatusItem] = []
        self.left_items: list[StatusItem] = []
        self.center_items: list[StatusItem] = []
        self.right_items: list[StatusItem] = []
        self.height: int = 1
        self.show_timestamp: bool = True

    def set_left(self, label: str, value: str, status: str = "normal",
                 icon: str = ""):
        self._set_section(self.left_items, label, value, status, icon)

    def set_center(self, label: str, value: str, status: str = "normal",
                   icon: str = ""):
        self._set_section(self.center_items, label, value, status, icon)

    def set_right(self, label: str, value: str, status: str = "normal",
                  icon: str = ""):
        self._set_section(self.right_items, label, value, status, icon)

    def _set_section(self, section: list, label: str, value: str,
                     status: str, icon: str):
        for item in section:
            if item.label == label:
                item.value = value
                item.status = status
                item.icon = icon
                return
        section.append(StatusItem(label=label, value=value, status=status, icon=icon))

    def add_item(self, label: str, value: str, status: str = "normal",
                 icon: str = "", position: str = "right", order: int = 0):
        item = StatusItem(label=label, value=value, status=status, icon=icon, order=order)
        self.items.append(item)
        if position == "left":
            self.left_items.append(item)
        elif position == "center":
            self.center_items.append(item)
        else:
            self.right_items.append(item)

    def remove_item(self, label: str):
        self.items = [i for i in self.items if i.label != label]
        self.left_items = [i for i in self.left_items if i.label != label]
        self.center_items = [i for i in self.center_items if i.label != label]
        self.right_items = [i for i in self.right_items if i.label != label]

    def get_item(self, label: str) -> Optional[StatusItem]:
        for item in self.items:
            if item.label == label:
                return item
        return None

    def _render_item(self, item: StatusItem) -> str:
        icon = f"{item.icon} " if item.icon else ""
        status_char = {"warning": "⚠", "error": "✗", "success": "✓", "normal": ""}.get(item.status, "")
        return f"{icon}{item.label}: {item.value} {status_char}".strip()

    def render(self) -> str:
        left = " | ".join(self._render_item(i) for i in self.left_items)
        center = " | ".join(self._render_item(i) for i in self.center_items)
        right = " | ".join(self._render_item(i) for i in self.right_items)

        ts = ""
        if self.show_timestamp:
            ts = datetime.now(timezone.utc).strftime("%H:%M:%S")

        parts = [left, center, right, ts]
        parts = [p for p in parts if p]
        return " ".join(parts)

    def render_compact(self) -> str:
        parts = []
        for item in self.items[:5]:
            parts.append(f"{item.label}={item.value}")
        return " | ".join(parts)

    def render_full_bar(self, width: int = 80) -> str:
        left = " | ".join(self._render_item(i) for i in self.left_items[:3])
        right = " | ".join(self._render_item(i) for i in self.right_items[:3])
        padding = width - len(left) - len(right) - 4
        if padding < 0:
            padding = 0
        return f" {left}{' ' * padding}{right} "

    def set_system_status(self, status: str):
        status_config = {
            "operational": ("✓", "success", "System Operational"),
            "degraded": ("⚠", "warning", "System Degraded"),
            "error": ("✗", "error", "System Error"),
            "offline": ("○", "error", "System Offline"),
        }
        icon, stat, label = status_config.get(status, ("?", "normal", status))
        self.set_left("System", label, stat, icon)

    def set_mission_info(self, mission_name: str, progress: float):
        self.set_center("Mission", f"{mission_name} ({progress:.0f}%)")

    def set_memory_info(self, count: int, usage_pct: float = 0):
        status = "warning" if usage_pct > 80 else "normal"
        self.set_right("Memory", f"{count} items ({usage_pct:.0f}%)", status)

    def get_stats(self) -> dict:
        return {
            "total_items": len(self.items),
            "left_items": len(self.left_items),
            "center_items": len(self.center_items),
            "right_items": len(self.right_items),
        }
