"""Context Builder — Build comprehensive context for agent decisions"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentContext:
    mission_goal: str = ""
    mission_id: str = ""
    current_task: str = ""
    task_id: str = ""
    task_description: str = ""
    available_tools: list[str] = field(default_factory=list)
    recent_actions: list[dict] = field(default_factory=list)
    recent_observations: list[str] = field(default_factory=list)
    memories: list[dict] = field(default_factory=list)
    facts: list[dict] = field(default_factory=list)
    risks: list[dict] = field(default_factory=list)
    pending_approvals: list[dict] = field(default_factory=list)
    progress: float = 0.0
    errors: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    def to_prompt_context(self) -> str:
        sections = []
        if self.mission_goal:
            sections.append(f"MISSION: {self.mission_goal}")
        if self.current_task:
            sections.append(f"CURRENT TASK: {self.current_task}")
        if self.task_description:
            sections.append(f"TASK DETAILS: {self.task_description}")
        if self.available_tools:
            sections.append(f"AVAILABLE TOOLS: {', '.join(self.available_tools)}")
        if self.recent_actions:
            recent = self.recent_actions[-5:]
            sections.append(f"RECENT ACTIONS: {self._format_actions(recent)}")
        if self.memories:
            sections.append(f"RELEVANT MEMORIES: {self._format_memories()}")
        if self.risks:
            sections.append(f"ACTIVE RISKS: {self._format_risks()}")
        if self.errors:
            sections.append(f"RECENT ERRORS: {'; '.join(self.errors[-3:])}")
        if self.constraints:
            sections.append(f"CONSTRAINTS: {'; '.join(self.constraints)}")
        sections.append(f"PROGRESS: {self.progress:.0f}%")
        return "\n\n".join(sections)

    def _format_actions(self, actions: list[dict]) -> str:
        formatted = []
        for a in actions:
            tool = a.get("tool", "?")
            success = "✓" if a.get("success") else "✗"
            formatted.append(f"{success} {tool}")
        return " → ".join(formatted) if formatted else "None"

    def _format_memories(self) -> str:
        return "; ".join(m.get("content", "")[:100] for m in self.memories[:3])

    def _format_risks(self) -> str:
        return "; ".join(f"{r.get('title', '?')} ({r.get('level', '?')})" for r in self.risks[:3])

    def to_dict(self) -> dict:
        return {
            "mission_goal": self.mission_goal,
            "mission_id": self.mission_id,
            "current_task": self.current_task,
            "task_id": self.task_id,
            "available_tools": self.available_tools,
            "recent_actions_count": len(self.recent_actions),
            "memories_count": len(self.memories),
            "risks_count": len(self.risks),
            "progress": self.progress,
            "errors_count": len(self.errors),
        }


class ContextBuilder:
    """Build agent context from various sources."""

    def __init__(self):
        self.mission_store = None
        self.memory_store = None
        self.risk_register = None

    def build(self, mission_id: str = None, task_id: str = None) -> AgentContext:
        ctx = AgentContext()

        if mission_id and self.mission_store:
            mission = self._load_mission(mission_id)
            ctx.mission_id = mission_id
            ctx.mission_goal = mission.get("goal", "")
            ctx.progress = mission.get("progress", 0)

        if task_id and self.mission_store:
            task = self._load_task(task_id)
            ctx.task_id = task_id
            ctx.current_task = task.get("title", "")
            ctx.task_description = task.get("description", "")

        if self.memory_store:
            ctx.memories = self._load_relevant_memories(mission_id, task_id)
            ctx.facts = self._load_relevant_facts(ctx.current_task)

        if self.risk_register and mission_id:
            ctx.risks = self._load_mission_risks(mission_id)

        return ctx

    def _load_mission(self, mission_id: str) -> dict:
        return {"goal": "", "progress": 0}

    def _load_task(self, task_id: str) -> dict:
        return {"title": "", "description": ""}

    def _load_relevant_memories(self, mission_id: str, task_id: str) -> list[dict]:
        return []

    def _load_relevant_facts(self, query: str) -> list[dict]:
        return []

    def _load_mission_risks(self, mission_id: str) -> list[dict]:
        return []
