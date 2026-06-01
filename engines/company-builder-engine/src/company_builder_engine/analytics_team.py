"""Analytics Team — Plan analytics tasks"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class AnalyticsTaskType(Enum):
    DATA_INFRASTRUCTURE = "data_infrastructure"
    DASHBOARDS = "dashboards"
    REPORTING = "reporting"
    DATA_GOVERNANCE = "data_governance"
    PREDICTIVE_ANALYTICS = "predictive_analytics"


@dataclass
class AnalyticsTask:
    id: str = field(default_factory=lambda: f"ANA-{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    task_type: AnalyticsTaskType = AnalyticsTaskType.DATA_INFRASTRUCTURE
    priority: int = 0
    estimated_hours: float = 0
    status: str = "todo"
    assigned_to: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "type": self.task_type.value, "priority": self.priority, "estimated_hours": self.estimated_hours, "status": self.status}


@dataclass
class AnalyticsPlan:
    id: str = field(default_factory=lambda: f"ANAPLAN-{uuid.uuid4().hex[:8]}")
    tasks: list[AnalyticsTask] = field(default_factory=list)
    data_strategy: dict = field(default_factory=dict)
    metrics_framework: dict = field(default_factory=dict)
    tools: dict = field(default_factory=dict)
    estimated_total_hours: float = 0
    team_size: int = 0
    sprint_plan: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {"id": self.id, "tasks_count": len(self.tasks), "total_hours": self.estimated_total_hours}


class AnalyticsTeam:
    def __init__(self):
        self.plans: dict[str, AnalyticsPlan] = {}
        self.tasks: dict[str, AnalyticsTask] = {}

    def plan(self, analytics_plan: dict, requirements: list[str]) -> AnalyticsPlan:
        plan = AnalyticsPlan(team_size=analytics_plan.get("team_size", 2))
        plan.tasks = self._create_tasks(requirements)
        for task in plan.tasks:
            self.tasks[task.id] = task
        plan.data_strategy = self._create_data_strategy()
        plan.metrics_framework = self._create_metrics_framework()
        plan.tools = self._setup_tools()
        plan.estimated_total_hours = sum(t.estimated_hours for t in plan.tasks)
        plan.sprint_plan = self._create_sprint_plan(plan.tasks, plan.team_size)
        self.plans[plan.id] = plan
        return plan

    def _create_tasks(self, requirements: list[str]) -> list[AnalyticsTask]:
        tasks = []
        task_list = [
            ("Data Warehouse Setup", AnalyticsTaskType.DATA_INFRASTRUCTURE, 32),
            ("ETL Pipeline", AnalyticsTaskType.DATA_INFRASTRUCTURE, 24),
            ("Executive Dashboard", AnalyticsTaskType.DASHBOARDS, 20),
            ("Product Analytics Dashboard", AnalyticsTaskType.DASHBOARDS, 20),
            ("Automated Reporting", AnalyticsTaskType.REPORTING, 16),
            ("Data Quality Framework", AnalyticsTaskType.DATA_GOVERNANCE, 16),
            ("Predictive Models", AnalyticsTaskType.PREDICTIVE_ANALYTICS, 32),
        ]
        for name, task_type, hours in task_list:
            task = AnalyticsTask(name=name, description=f"Implement {name.lower()}", task_type=task_type, priority=len(tasks) + 1, estimated_hours=hours)
            tasks.append(task)
        return tasks

    def _create_data_strategy(self) -> dict:
        return {"data_sources": ["Product", "Marketing", "Sales", "Support"], "data_quality": "Automated validation", "retention": "7 years"}

    def _create_metrics_framework(self) -> dict:
        return {"north_star_metric": "Monthly Active Users", "categories": {"acquisition": ["CAC", "Conversion Rate"], "activation": ["Onboarding Completion"], "retention": ["DAU/MAU", "Churn Rate"], "revenue": ["ARPU", "LTV"], "referral": ["NPS", "Referral Rate"]}}

    def _setup_tools(self) -> dict:
        return {"data_warehouse": "Snowflake", "bi_tool": "Metabase", "analytics": "Mixpanel", "etl": "dbt", "orchestration": "Airflow"}

    def _create_sprint_plan(self, tasks: list[AnalyticsTask], team_size: int) -> list[dict]:
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

    def get_analytics_insights(self) -> dict:
        all_plans = list(self.plans.values())
        if not all_plans:
            return {"status": "no_plans"}
        return {"total_plans": len(all_plans), "total_tasks": sum(len(p.tasks) for p in all_plans)}