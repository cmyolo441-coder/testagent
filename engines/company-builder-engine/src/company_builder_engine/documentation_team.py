"""Documentation Team — Plan documentation tasks"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class DocTaskType(Enum):
    API_DOCUMENTATION = "api_documentation"
    USER_DOCUMENTATION = "user_documentation"
    TECHNICAL_DOCUMENTATION = "technical_documentation"
    INTERNAL_DOCUMENTATION = "internal_documentation"


@dataclass
class DocTask:
    id: str = field(default_factory=lambda: f"DOC-{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    task_type: DocTaskType = DocTaskType.API_DOCUMENTATION
    priority: int = 0
    estimated_hours: float = 0
    actual_hours: float = 0
    status: str = "todo"
    assigned_to: str = ""
    format: str = "markdown"
    audience: str = "developers"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.task_type.value,
            "priority": self.priority,
            "estimated_hours": self.estimated_hours,
            "status": self.status,
        }


@dataclass
class DocPlan:
    id: str = field(default_factory=lambda: f"DOCPLAN-{uuid.uuid4().hex[:8]}")
    tasks: list[DocTask] = field(default_factory=list)
    documentation_structure: dict = field(default_factory=dict)
    style_guide: dict = field(default_factory=dict)
    tools: dict = field(default_factory=dict)
    estimated_total_hours: float = 0
    team_size: int = 0
    sprint_plan: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tasks_count": len(self.tasks),
            "total_hours": self.estimated_total_hours,
        }


class DocumentationTeam:
    """Plan and coordinate documentation tasks."""

    def __init__(self):
        self.plans: dict[str, DocPlan] = {}
        self.tasks: dict[str, DocTask] = {}

    def plan(self, docs_plan: dict, requirements: list[str]) -> DocPlan:
        """Plan documentation activities."""
        plan = DocPlan(
            team_size=docs_plan.get("team_size", 2)
        )
        
        plan.tasks = self._create_tasks(requirements)
        for task in plan.tasks:
            self.tasks[task.id] = task
        
        plan.documentation_structure = self._create_doc_structure()
        plan.style_guide = self._create_style_guide()
        plan.tools = self._setup_tools()
        plan.estimated_total_hours = sum(t.estimated_hours for t in plan.tasks)
        plan.sprint_plan = self._create_sprint_plan(plan.tasks, plan.team_size)
        
        self.plans[plan.id] = plan
        return plan

    def _create_tasks(self, requirements: list[str]) -> list[DocTask]:
        tasks = []
        
        task_list = [
            ("API Reference Documentation", DocTaskType.API_DOCUMENTATION, 24),
            ("Getting Started Guide", DocTaskType.USER_DOCUMENTATION, 16),
            ("User Manual", DocTaskType.USER_DOCUMENTATION, 40),
            ("Architecture Documentation", DocTaskType.TECHNICAL_DOCUMENTATION, 20),
            ("Deployment Guide", DocTaskType.TECHNICAL_DOCUMENTATION, 16),
            ("Contributing Guidelines", DocTaskType.INTERNAL_DOCUMENTATION, 8),
            ("Security Documentation", DocTaskType.TECHNICAL_DOCUMENTATION, 12),
            ("FAQ Documentation", DocTaskType.USER_DOCUMENTATION, 12),
        ]
        
        for name, task_type, hours in task_list:
            task = DocTask(
                name=name,
                description=f"Create {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                audience="developers" if task_type == DocTaskType.API_DOCUMENTATION else "users",
            )
            tasks.append(task)
        
        return tasks

    def _create_doc_structure(self) -> dict:
        return {
            "sections": {
                "getting_started": ["Installation", "Quick Start", "Configuration"],
                "user_guide": ["Features", "Tutorials", "Examples"],
                "api_reference": ["Endpoints", "Authentication", "Error Codes"],
                "advanced": ["Architecture", "Customization", "Troubleshooting"],
            },
            "formats": ["Markdown", "HTML", "PDF"],
            "hosting": "GitHub Pages",
        }

    def _create_style_guide(self) -> dict:
        return {
            "tone": "Clear and concise",
            "language": "Technical but accessible",
            "structure": "Hierarchical with cross-references",
            "code_examples": "Always include working examples",
            "screenshots": "Include for UI-related documentation",
        }

    def _setup_tools(self) -> dict:
        return {
            "documentation_tool": "MkDocs",
            "api_doc_tool": "Swagger/OpenAPI",
            "diagrams": "Mermaid",
            "version_control": "Git",
            "ci_cd": "GitHub Actions",
        }

    def _create_sprint_plan(self, tasks: list[DocTask], team_size: int) -> list[dict]:
        sprints = []
        sprint_capacity = team_size * 40
        current_sprint = []
        current_hours = 0
        sprint_number = 1
        
        for task in sorted(tasks, key=lambda t: t.priority):
            if current_hours + task.estimated_hours > sprint_capacity and current_sprint:
                sprints.append({
                    "sprint_number": sprint_number,
                    "tasks": [t.to_dict() for t in current_sprint],
                    "total_hours": current_hours,
                })
                current_sprint = []
                current_hours = 0
                sprint_number += 1
            current_sprint.append(task)
            current_hours += task.estimated_hours
        
        if current_sprint:
            sprints.append({
                "sprint_number": sprint_number,
                "tasks": [t.to_dict() for t in current_sprint],
                "total_hours": current_hours,
            })
        
        return sprints

    def get_doc_insights(self) -> dict:
        all_plans = list(self.plans.values())
        if not all_plans:
            return {"status": "no_plans"}
        
        total_tasks = sum(len(p.tasks) for p in all_plans)
        total_hours = sum(t.estimated_hours for p in all_plans for t in p.tasks)
        
        return {
            "total_plans": len(all_plans),
            "total_tasks": total_tasks,
            "total_hours": total_hours,
        }