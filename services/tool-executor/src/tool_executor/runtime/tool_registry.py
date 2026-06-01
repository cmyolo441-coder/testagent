"""Tool Registry — Register, discover, and manage tools"""
from dataclasses import dataclass, field
from typing import Callable, Any, Optional
from enum import Enum


class ToolCategory(Enum):
    FILESYSTEM = "filesystem"
    SHELL = "shell"
    GIT = "git"
    BROWSER = "browser"
    DATABASE = "database"
    CLOUD = "cloud"
    DEPLOYMENT = "deployment"
    NETWORK = "network"
    ANALYSIS = "analysis"
    CUSTOM = "custom"


@dataclass
class ToolDefinition:
    name: str
    description: str
    category: ToolCategory
    handler: Callable
    parameters: dict = field(default_factory=dict)
    risk_level: str = "low"
    requires_approval: bool = False
    timeout: int = 30
    enabled: bool = True
    version: str = "1.0.0"
    examples: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "risk_level": self.risk_level,
            "requires_approval": self.requires_approval,
            "timeout": self.timeout,
            "enabled": self.enabled,
            "version": self.version,
            "parameters": self.parameters,
        }


class ToolRegistry:
    """Central registry for all available tools."""

    def __init__(self):
        self.tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        self.tools[tool.name] = tool

    def register_function(self, name: str, handler: Callable, description: str = "",
                         category: ToolCategory = ToolCategory.CUSTOM,
                         risk_level: str = "low", **kwargs):
        tool = ToolDefinition(
            name=name,
            description=description,
            category=category,
            handler=handler,
            risk_level=risk_level,
            **kwargs,
        )
        self.register(tool)

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self.tools.get(name)

    def list_tools(self, category: ToolCategory = None, enabled_only: bool = True) -> list[ToolDefinition]:
        tools = list(self.tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        return tools

    def search(self, query: str) -> list[ToolDefinition]:
        q = query.lower()
        return [
            t for t in self.tools.values()
            if q in t.name.lower() or q in t.description.lower()
        ]

    def get_categories(self) -> dict[str, int]:
        categories = {}
        for tool in self.tools.values():
            cat = tool.category.value
            categories[cat] = categories.get(cat, 0) + 1
        return categories
