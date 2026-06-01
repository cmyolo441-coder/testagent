"""Support Team — Plan customer support tasks"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class SupportTaskType(Enum):
    SUPPORT_SETUP = "support_setup"
    DOCUMENTATION = "documentation"
    TRAINING = "training"
    PROCESS = "process"
    TOOLS = "tools"


@dataclass
class SupportTask:
    id: str = field(default_factory=lambda: f"SUP-{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    task_type: SupportTaskType = SupportTaskType.SUPPORT_SETUP
    priority: int = 0
    estimated_hours: float = 0
    status: str = "todo"
    assigned_to: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "type": self.task_type.value, "priority": self.priority, "estimated_hours": self.estimated_hours, "status": self.status}


@dataclass
class SupportPlan:
    id: str = field(default_factory=lambda: f"SUPPLAN-{uuid.uuid4().hex[:8]}")
    tasks: list[SupportTask] = field(default_factory=list)
    strategy: dict = field(default_factory=dict)
    channels: dict = field(default_factory=dict)
    sla: dict = field(default_factory=dict)
    estimated_total_hours: float = 0
    team_size: int = 0
    sprint_plan: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {"id": self.id, "tasks_count": len(self.tasks), "total_hours": self.estimated_total_hours}


class SupportTeam:
    def __init__(self):
        self.plans: dict[str, SupportPlan] = {}
        self.tasks: dict[str, SupportTask] = {}

    def plan(self, support_plan: dict, requirements: list[str]) -> SupportPlan:
        plan = SupportPlan(team_size=support_plan.get("team_size", 2))
        plan.tasks = self._create_tasks(requirements)
        for task in plan.tasks:
            self.tasks[task.id] = task
        plan.strategy = self._create_strategy()
        plan.channels = self._plan_channels()
        plan.sla = self._define_sla()
        plan.estimated_total_hours = sum(t.estimated_hours for t in plan.tasks)
        plan.sprint_plan = self._create_sprint_plan(plan.tasks, plan.team_size)
        self.plans[plan.id] = plan
        return plan

    def _create_tasks(self, requirements: list[str]) -> list[SupportTask]:
        tasks = []
        task_list = [
            ("Help Center Setup", SupportTaskType.SUPPORT_SETUP, 16),
            ("Knowledge Base Creation", SupportTaskType.DOCUMENTATION, 24),
            ("Support Ticketing System", SupportTaskType.TOOLS, 12),
            ("Support Team Training", SupportTaskType.TRAINING, 16),
            ("Escalation Process", SupportTaskType.PROCESS, 8),
            ("Customer Onboarding Guide", SupportTaskType.DOCUMENTATION, 12),
        ]
        for name, task_type, hours in task_list:
            task = SupportTask(name=name, description=f"Create {name.lower()}", task_type=task_type, priority=len(tasks) + 1, estimated_hours=hours)
            tasks.append(task)
        return tasks

    def _create_strategy(self) -> dict:
        return {"channels": ["Email", "Chat", "Phone", "Self-service"], "hours": "24/7 for critical issues", "model": "Tiered support with escalation"}

    def _plan_channels(self) -> dict:
        return {"email": {"response_time": "4 hours", "availability": "24/7"}, "chat": {"response_time": "5 minutes", "availability": "Business hours"}, "phone": {"response_time": "Immediate", "availability": "Business hours"}}

    def _define_sla(self) -> dict:
        return {"critical": {"response": "1 hour", "resolution": "4 hours"}, "high": {"response": "4 hours", "resolution": "24 hours"}, "medium": {"response": "8 hours", "resolution": "3 days"}, "low": {"response": "24 hours", "resolution": "5 days"}}

    def _create_sprint_plan(self, tasks: list[SupportTask], team_size: int) -> list[dict]:
        sprints = []
        sprint_capacity = team_size * 40
        current_sprint = []
        current_hours = 0
        sprint_number = 1
        for task in sorted(tasks, key=lambda t: t.priority):
            if current_hours + task.estimated_hours > sprint_capacity and current_sprint:
                sprints.append({"sprint_number": sprint_number, "tasks": [t.to_dict() for t in current_sprint], "total_hours": current_hours})
                current_sprint = []
                current_hours = 0
                sprint_number += 1
            current_sprint.append(task)
            current_hours += task.estimated_hours
        if current_sprint:
            sprints.append({"sprint_number": sprint_number, "tasks": [t.to_dict() for t in current_sprint], "total_hours": current_hours})
        return sprints

    def get_support_insights(self) -> dict:
        all_plans = list(self.plans.values())
        if not all_plans:
            return {"status": "no_plans"}
        return {"total_plans": len(all_plans), "total_tasks": sum(len(p.tasks) for p in all_plans)}