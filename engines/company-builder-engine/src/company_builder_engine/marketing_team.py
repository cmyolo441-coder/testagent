"""Marketing Team — Plan marketing tasks"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class MarketingTaskType(Enum):
    CONTENT_MARKETING = "content_marketing"
    SEO = "seo"
    PAID_ADVERTISING = "paid_advertising"
    SOCIAL_MEDIA = "social_media"
    EMAIL_MARKETING = "email_marketing"
    PR = "pr"
    EVENTS = "events"


@dataclass
class MarketingTask:
    id: str = field(default_factory=lambda: f"MKT-{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    task_type: MarketingTaskType = MarketingTaskType.CONTENT_MARKETING
    priority: int = 0
    estimated_hours: float = 0
    budget: float = 0
    status: str = "todo"
    assigned_to: str = ""
    kpis: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.task_type.value,
            "priority": self.priority,
            "estimated_hours": self.estimated_hours,
            "budget": self.budget,
            "status": self.status,
        }


@dataclass
class MarketingPlan:
    id: str = field(default_factory=lambda: f"MKTPLAN-{uuid.uuid4().hex[:8]}")
    tasks: list[MarketingTask] = field(default_factory=list)
    strategy: dict = field(default_factory=dict)
    channels: dict = field(default_factory=dict)
    budget_allocation: dict = field(default_factory=dict)
    estimated_total_hours: float = 0
    total_budget: float = 0
    team_size: int = 0
    sprint_plan: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tasks_count": len(self.tasks),
            "total_hours": self.estimated_total_hours,
            "total_budget": self.total_budget,
        }


class MarketingTeam:
    """Plan and coordinate marketing tasks."""

    def __init__(self):
        self.plans: dict[str, MarketingPlan] = {}
        self.tasks: dict[str, MarketingTask] = {}

    def plan(self, marketing_plan: dict, requirements: list[str]) -> MarketingPlan:
        plan = MarketingPlan(
            team_size=marketing_plan.get("team_size", 3),
            total_budget=marketing_plan.get("budget", 50000)
        )
        
        plan.tasks = self._create_tasks(requirements)
        for task in plan.tasks:
            self.tasks[task.id] = task
        
        plan.strategy = self._create_strategy(requirements)
        plan.channels = self._plan_channels()
        plan.budget_allocation = self._allocate_budget(plan.total_budget)
        plan.estimated_total_hours = sum(t.estimated_hours for t in plan.tasks)
        plan.sprint_plan = self._create_sprint_plan(plan.tasks, plan.team_size)
        
        self.plans[plan.id] = plan
        return plan

    def _create_tasks(self, requirements: list[str]) -> list[MarketingTask]:
        tasks = []
        task_list = [
            ("Content Strategy", MarketingTaskType.CONTENT_MARKETING, 16, 2000),
            ("Blog Posts", MarketingTaskType.CONTENT_MARKETING, 24, 3000),
            ("SEO Optimization", MarketingTaskType.SEO, 20, 2500),
            ("PPC Campaign Setup", MarketingTaskType.PAID_ADVERTISING, 16, 10000),
            ("Social Media Strategy", MarketingTaskType.SOCIAL_MEDIA, 12, 1500),
            ("Email Campaign Setup", MarketingTaskType.EMAIL_MARKETING, 12, 1000),
            ("PR Outreach", MarketingTaskType.PR, 20, 5000),
        ]
        
        for name, task_type, hours, budget in task_list:
            task = MarketingTask(
                name=name,
                description=f"Implement {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                budget=budget,
                kpis=["Awareness", "Leads", "Conversions"],
            )
            tasks.append(task)
        
        return tasks

    def _create_strategy(self, requirements: list[str]) -> dict:
        return {
            "target_audience": "Tech-savvy professionals",
            "positioning": "Innovative solution for modern teams",
            "messaging": ["Save time", "Increase productivity", "Reduce costs"],
            "channels": ["Content", "Social", "Email", "Paid"],
        }

    def _plan_channels(self) -> dict:
        return {
            "organic": {"content_marketing": 0.4, "seo": 0.3, "social_media": 0.3},
            "paid": {"ppc": 0.5, "social_ads": 0.3, "display": 0.2},
        }

    def _allocate_budget(self, total: float) -> dict:
        return {
            "content_marketing": total * 0.25,
            "paid_advertising": total * 0.35,
            "social_media": total * 0.15,
            "seo": total * 0.10,
            "email_marketing": total * 0.05,
            "pr": total * 0.10,
        }

    def _create_sprint_plan(self, tasks: list[MarketingTask], team_size: int) -> list[dict]:
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

    def get_marketing_insights(self) -> dict:
        all_plans = list(self.plans.values())
        if not all_plans:
            return {"status": "no_plans"}
        
        total_tasks = sum(len(p.tasks) for p in all_plans)
        total_hours = sum(t.estimated_hours for p in all_plans for t in p.tasks)
        total_budget = sum(p.total_budget for p in all_plans)
        
        return {
            "total_plans": len(all_plans),
            "total_tasks": total_tasks,
            "total_hours": total_hours,
            "total_budget": total_budget,
        }