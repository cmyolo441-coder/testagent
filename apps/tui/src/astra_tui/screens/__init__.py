"""ASTRA TUI Screens Package"""
from astra_tui.screens.command_center import CommandCenterScreen
from astra_tui.screens.mission_control import MissionControlScreen
from astra_tui.screens.agent_civilization import AgentCivilizationScreen
from astra_tui.screens.truth_panel import TruthPanelScreen
from astra_tui.screens.memory_galaxy import MemoryGalaxyScreen
from astra_tui.screens.science_lab import ScienceLabScreen
from astra_tui.screens.math_lab import MathLabScreen
from astra_tui.screens.company_builder import CompanyBuilderScreen
from astra_tui.screens.risk_approval import RiskApprovalScreen
from astra_tui.screens.tool_stream import ToolStreamScreen
from astra_tui.screens.knowledge_graph import KnowledgeGraphScreen
from astra_tui.screens.audit_replay import AuditReplayScreen

SCREEN_REGISTRY = {
    "command_center": CommandCenterScreen,
    "mission_control": MissionControlScreen,
    "agent_civilization": AgentCivilizationScreen,
    "truth_panel": TruthPanelScreen,
    "memory_galaxy": MemoryGalaxyScreen,
    "science_lab": ScienceLabScreen,
    "math_lab": MathLabScreen,
    "company_builder": CompanyBuilderScreen,
    "risk_approval": RiskApprovalScreen,
    "tool_stream": ToolStreamScreen,
    "knowledge_graph": KnowledgeGraphScreen,
    "audit_replay": AuditReplayScreen,
}

__all__ = [
    "CommandCenterScreen", "MissionControlScreen", "AgentCivilizationScreen",
    "TruthPanelScreen", "MemoryGalaxyScreen", "ScienceLabScreen",
    "MathLabScreen", "CompanyBuilderScreen", "RiskApprovalScreen",
    "ToolStreamScreen", "KnowledgeGraphScreen", "AuditReplayScreen",
    "SCREEN_REGISTRY",
]
