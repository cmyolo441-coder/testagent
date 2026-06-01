"""Sales Team — Plan sales tasks"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class SalesTaskType(Enum):
    LEAD_GENERATION = "lead_generation"
    SALES_PROCESS = "sales_process"
    CRM_SETUP = "crm_setup"
    SALES_ENABLEMENT = "sales_enablement"
    PARTNERSHIPS = "partnerships"


@dataclass
class SalesTask:
    id: str = field(default_factory=lambda: f"SALES-{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    task_type: SalesTaskType = SalesTaskType.LEAD_GENERATION
    priority: int = 0
    estimated_hours: float = 0
    status: str = "todo"
    assigned_to: str = ""
    target: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "type": self.task_type.value, "priority": self.priority, "estimated_hours": self.estimated_hours, "status": self.status}


@dataclass
class SalesPlan:
    id: str = field(default_factory=lambda: f"SALESPLAN-{uuid.uuid4().hex[:8]}")
    tasks: list[SalesTask] = field(default_factory=list)
    strategy: dict = field(default_factory=dict)
    pipeline: dict = field(default_factory=dict)
    estimated_total_hours: float = 0
    team_size: int = 0
    sprint_plan: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {"id": self.id, "tasks_count": len(self.tasks), "total_hours": self.estimated_total_hours}


class SalesTeam:
    def __init__(self):
        self.plans: dict[str, SalesPlan] = {}
        self.tasks: dict[str, SalesTask] = {}

    def plan(self, sales_plan: dict, requirements: list[str]) -> SalesPlan:
        plan = SalesPlan(team_size=sales_plan.get("team_size", 3))
        plan.tasks = self._create_tasks(requirements)
        for task in plan.tasks:
            self.tasks[task.id] = task
        plan.strategy = self._create_strategy()
        plan.pipeline = self._create_pipeline()
        plan.estimated_total_hours = sum(t.estimated_hours for t in plan.tasks)
        plan.sprint_plan = self._create_sprint_plan(plan.tasks, plan.team_size)
        self.plans[plan.id] = plan
        return plan

    def _create_tasks(self, requirements: list[str]) -> list[SalesTask]:
        tasks = []
        task_list = [
            ("Lead Generation Strategy", SalesTaskType.LEAD_GENERATION, 16),
            ("Outbound Campaign Setup", SalesTaskType.LEAD_GENERATION, 20),
            ("Sales CRM Setup", SalesTaskType.CRM_SETUP, 12),
            ("Sales Process Documentation", SalesTaskType.SALES_PROCESS, 16),
            ("Sales Collateral", SalesTaskType.SALES_ENABLEMENT, 20),
            ("Partner Program Setup", SalesTaskType.PARTNERSHIPS, 24),
        ]
        for name, task_type, hours in task_list:
            task = SalesTask(name=name, description=f"Implement {name.lower()}", task_type=task_type, priority=len(tasks) + 1, estimated_hours=hours, target="Revenue growth")
            tasks.append(task)
        return tasks

    def _create_strategy(self) -> dict:
        return {"target_market": "SMB and Mid-Market", "sales_model": "Product-led + Sales-assisted", "pricing": "Tiered subscription"}

    def _create_pipeline(self) -> dict:
        return {"stages": ["Lead", "Qualified", "Demo", "Proposal", "Negotiation", "Closed Won"], "conversion_rates": {"lead_to_qualified": 0.25, "qualified_to_demo": 0.5, "demo_to_proposal": 0.6, "proposal_to_close": 0.4}}

    def _create_sprint_plan(self, tasks: list[SalesTask], team_size: int) -> list[dict]:
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

    def get_sales_insights(self) -> dict:
        all_plans = list(self.plans.values())
        if not all_plans:
            return {"status": "no_plans"}
        return {"total_plans": len(all_plans), "total_tasks": sum(len(p.tasks) for p in all_plans)}