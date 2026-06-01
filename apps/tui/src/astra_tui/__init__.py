"""ASTRA TUI — Beautiful Terminal Dashboard for ASTRA Command OS"""

from astra_tui.theme import AstraTheme, ColorPalette, THEME_DARK, THEME_LIGHT
from astra_tui.keybindings import KeyBindings, KeyBinding
from astra_tui.app import AstraDashboard, DashboardConfig

from astra_tui.screens import (
    CommandCenterScreen, MissionControlScreen, AgentCivilizationScreen,
    TruthPanelScreen, MemoryGalaxyScreen, ScienceLabScreen,
    MathLabScreen, CompanyBuilderScreen, RiskApprovalScreen,
    ToolStreamScreen, KnowledgeGraphScreen, AuditReplayScreen,
    SCREEN_REGISTRY,
)

from astra_tui.widgets import (
    MissionTimeline, ObjectiveTreeView, AgentMap,
    ConfidenceMeter, VerificationEvidence, MemoryBrowser,
    ApprovalModal, DiffViewer, LiveLogs, StatusBar,
)

__all__ = [
    "AstraTheme", "ColorPalette", "THEME_DARK", "THEME_LIGHT",
    "KeyBindings", "KeyBinding",
    "AstraDashboard", "DashboardConfig",
    "CommandCenterScreen", "MissionControlScreen", "AgentCivilizationScreen",
    "TruthPanelScreen", "MemoryGalaxyScreen", "ScienceLabScreen",
    "MathLabScreen", "CompanyBuilderScreen", "RiskApprovalScreen",
    "ToolStreamScreen", "KnowledgeGraphScreen", "AuditReplayScreen",
    "SCREEN_REGISTRY",
    "MissionTimeline", "ObjectiveTreeView", "AgentMap",
    "ConfidenceMeter", "VerificationEvidence", "MemoryBrowser",
    "ApprovalModal", "DiffViewer", "LiveLogs", "StatusBar",
]
