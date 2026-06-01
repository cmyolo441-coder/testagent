"""ASTRA TUI Keybindings — Keyboard shortcuts and navigation"""
from dataclasses import dataclass, field


@dataclass
class KeyBinding:
    key: str
    action: str
    description: str
    category: str = "general"
    ctrl: bool = False
    shift: bool = False
    alt: bool = False

    def __str__(self) -> str:
        parts = []
        if self.ctrl:
            parts.append("Ctrl")
        if self.shift:
            parts.append("Shift")
        if self.alt:
            parts.append("Alt")
        parts.append(self.key.upper())
        return "+".join(parts)


@dataclass
class KeyBindings:
    bindings: dict[str, KeyBinding] = field(default_factory=dict)

    def __post_init__(self):
        self._register_defaults()

    def _register_defaults(self):
        defaults = [
            KeyBinding("q", "quit", "Quit application", "general"),
            KeyBinding("escape", "back", "Go back / close modal", "navigation"),
            KeyBinding("ctrl+c", "quit", "Force quit", "general"),
            KeyBinding("ctrl+r", "refresh", "Refresh current view", "general"),
            KeyBinding("ctrl+s", "save", "Save current state", "general"),
            KeyBinding("ctrl+z", "undo", "Undo last action", "general"),
            KeyBinding("/", "search", "Open search", "navigation"),
            KeyBinding("?", "help", "Show help", "general"),
            KeyBinding("1", "screen:command_center", "Go to Command Center", "screens", True),
            KeyBinding("2", "screen:mission_control", "Go to Mission Control", "screens", True),
            KeyBinding("3", "screen:agent_civilization", "Go to Agent Civilization", "screens", True),
            KeyBinding("4", "screen:truth_panel", "Go to Truth Panel", "screens", True),
            KeyBinding("5", "screen:memory_galaxy", "Go to Memory Galaxy", "screens", True),
            KeyBinding("6", "screen:science_lab", "Go to Science Lab", "screens", True),
            KeyBinding("7", "screen:math_lab", "Go to Math Lab", "screens", True),
            KeyBinding("8", "screen:company_builder", "Go to Company Builder", "screens", True),
            KeyBinding("9", "screen:risk_approval", "Go to Risk Approval", "screens", True),
            KeyBinding("0", "screen:tool_stream", "Go to Tool Stream", "screens", True),
            KeyBinding("tab", "next_panel", "Switch to next panel", "navigation"),
            KeyBinding("shift+tab", "prev_panel", "Switch to previous panel", "navigation"),
            KeyBinding("enter", "select", "Select / confirm", "action"),
            KeyBinding("space", "toggle", "Toggle selection / play/pause", "action"),
            KeyBinding("j", "down", "Move down", "navigation"),
            KeyBinding("k", "up", "Move up", "navigation"),
            KeyBinding("h", "left", "Move left", "navigation"),
            KeyBinding("l", "right", "Move right", "navigation"),
            KeyBinding("g", "top", "Go to top", "navigation"),
            KeyBinding("shift+g", "bottom", "Go to bottom", "navigation"),
            KeyBinding("ctrl+n", "new", "Create new item", "action"),
            KeyBinding("ctrl+d", "delete", "Delete selected item", "action"),
            KeyBinding("ctrl+e", "edit", "Edit selected item", "action"),
            KeyBinding("ctrl+a", "approve", "Approve selected", "action"),
            KeyBinding("ctrl+x", "reject", "Reject selected", "action"),
            KeyBinding("ctrl+l", "logs", "Toggle live logs", "view"),
            KeyBinding("ctrl+m", "memory", "Toggle memory panel", "view"),
            KeyBinding("ctrl+t", "timeline", "Toggle timeline", "view"),
            KeyBinding("f1", "help", "Show help", "general"),
            KeyBinding("f5", "refresh", "Refresh data", "general"),
            KeyBinding("f12", "debug", "Toggle debug mode", "general"),
        ]
        for binding in defaults:
            self.bindings[binding.key] = binding

    def register(self, key: str, action: str, description: str,
                 category: str = "general", ctrl: bool = False,
                 shift: bool = False, alt: bool = False):
        binding = KeyBinding(
            key=key, action=action, description=description,
            category=category, ctrl=ctrl, shift=shift, alt=alt,
        )
        self.bindings[key] = binding

    def get_action(self, key: str) -> str:
        binding = self.bindings.get(key)
        return binding.action if binding else ""

    def get_description(self, key: str) -> str:
        binding = self.bindings.get(key)
        return binding.description if binding else ""

    def get_by_category(self, category: str) -> list[KeyBinding]:
        return [b for b in self.bindings.values() if b.category == category]

    def get_all(self) -> list[KeyBinding]:
        return sorted(self.bindings.values(), key=lambda b: (b.category, b.key))

    def render_help(self) -> str:
        categories = {}
        for b in self.bindings.values():
            if b.category not in categories:
                categories[b.category] = []
            categories[b.category].append(b)

        lines = ["ASTRA TUI Keybindings", "=" * 40, ""]
        for cat in sorted(categories.keys()):
            lines.append(f"[{cat.upper()}]")
            for b in sorted(categories[cat], key=lambda x: x.key):
                lines.append(f"  {str(b):<20} {b.description}")
            lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            key: {
                "action": b.action,
                "description": b.description,
                "category": b.category,
            }
            for key, b in self.bindings.items()
        }
