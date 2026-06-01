"""Launch Orchestrator — Orchestrate product launch"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


@dataclass
class LaunchTask:
    id: str = field(default_factory=lambda: f"LAUNCH-{uuid.uuid4().hex[:8]}")
    name: str = ""
    team: str = ""
    status: str = "pending"
    dependencies: list[str] = field(default_factory=list)
    deadline: str = ""
    owner: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "team": self.team, "status": self.status}


@dataclass
class LaunchPlan:
    id: str = field(default_factory=lambda: f"LAUNCHPLAN-{uuid.uuid4().hex[:8]}")
    launch_date: str = ""
    tasks: list[LaunchTask] = field(default_factory=list)
    timeline: dict = field(default_factory=dict)
    checklist: list[dict] = field(default_factory=list)
    rollback_plan: dict = field(default_factory=dict)
    communication_plan: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {"id": self.id, "launch_date": self.launch_date, "tasks_count": len(self.tasks)}


class LaunchOrchestrator:
    """Orchestrate product launch across teams."""

    def __init__(self):
        self.plans: dict[str, LaunchPlan] = {}
        self.tasks: dict[str, LaunchTask] = {}

    def orchestrate(self, teams: list[str], timeline: dict) -> LaunchPlan:
        """Create launch plan orchestrating multiple teams."""
        plan = LaunchPlan(launch_date=timeline.get("launch_date", "2024-01-01"))
        
        plan.tasks = self._create_launch_tasks(teams)
        for task in plan.tasks:
            self.tasks[task.id] = task
        
        plan.timeline = self._create_timeline(timeline, plan.tasks)
        plan.checklist = self._create_launch_checklist(teams)
        plan.rollback_plan = self._create_rollback_plan()
        plan.communication_plan = self._create_communication_plan(teams)
        
        self.plans[plan.id] = plan
        return plan

    def _create_launch_tasks(self, teams: list[str]) -> list[LaunchTask]:
        tasks = []
        
        team_tasks = {
            "engineering": [("Final Code Freeze", "Code freeze 48h before launch"), ("Production Deployment", "Deploy to production environment"), ("Performance Testing", "Run load tests")],
            "qa": [("Final QA Sign-off", "Complete all test cases"), ("Regression Testing", "Run full regression suite")],
            "marketing": [("Launch Announcement", "Prepare press release and social posts"), ("Website Update", "Update website with launch info")],
            "sales": [("Sales Enablement", "Update sales materials"), ("Demo Environment", "Set up demo environment")],
            "support": [("Support Training", "Train support team on new features"), ("Documentation", "Update help center")],
            "devops": [("Infrastructure Scaling", "Scale production infrastructure"), ("Monitoring Setup", "Ensure monitoring is active")],
        }
        
        for team in teams:
            for task_name, description in team_tasks.get(team, []):
                task = LaunchTask(name=task_name, team=team, description=description)
                tasks.append(task)
        
        return tasks

    def _create_timeline(self, timeline: dict, tasks: list[LaunchTask]) -> dict:
        launch_date = timeline.get("launch_date", "2024-01-01")
        return {
            "t-14_days": ["Marketing materials finalized", "Sales training complete"],
            "t-7_days": ["Code freeze", "Final QA testing"],
            "t-3_days": ["Infrastructure scaling", "Support team briefed"],
            "t-1_day": ["Final checks", "Communication plan activated"],
            "launch_day": ["Production deployment", "Launch announcement", "Monitoring active"],
            "t+1_day": ["Monitor metrics", "Address issues"],
            "t+7_days": ["Post-launch review", "Gather feedback"],
        }

    def _create_launch_checklist(self, teams: list[str]) -> list[dict]:
        return [
            {"item": "Code freeze complete", "team": "engineering", "critical": True},
            {"item": "All tests passing", "team": "qa", "critical": True},
            {"item": "Production deployment successful", "team": "devops", "critical": True},
            {"item": "Monitoring and alerting active", "team": "devops", "critical": True},
            {"item": "Marketing materials published", "team": "marketing", "critical": False},
            {"item": "Sales team briefed", "team": "sales", "critical": False},
            {"item": "Support documentation updated", "team": "support", "critical": True},
            {"item": "Rollback plan tested", "team": "engineering", "critical": True},
        ]

    def _create_rollback_plan(self) -> dict:
        return {
            "triggers": ["Error rate > 5%", "Response time > 2s", "Data corruption detected"],
            "procedure": [
                "Stop traffic to new version",
                "Activate previous version",
                "Verify rollback success",
                "Notify team and stakeholders",
            ],
            "responsible": "DevOps team",
            "estimated_time": "15 minutes",
        }

    def _create_communication_plan(self, teams: list[str]) -> dict:
        return {
            "internal": {
                "channels": ["Slack #launch", "Email", "Phone bridge"],
                "updates": "Every hour during launch",
            },
            "external": {
                "channels": ["Twitter", "Blog", "Email newsletter"],
                "timing": "Launch announcement at launch time",
            },
            "escalation": {
                "issues": "Immediate notification to team leads",
                "critical_issues": "All-hands call within 15 minutes",
            },
        }

    def update_task_status(self, task_id: str, status: str) -> dict:
        task = self.tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        task.status = status
        return {"status": "updated", "task": task.to_dict()}

    def get_launch_readiness(self, plan_id: str) -> dict:
        plan = self.plans.get(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        
        completed = sum(1 for t in plan.tasks if t.status == "completed")
        total = len(plan.tasks)
        
        return {
            "readiness_score": completed / total * 100 if total > 0 else 0,
            "completed_tasks": completed,
            "total_tasks": total,
            "tasks_by_team": {team: sum(1 for t in plan.tasks if t.team == team and t.status == "completed") for team in set(t.team for t in plan.tasks)},
        }

    def get_launch_insights(self) -> dict:
        all_plans = list(self.plans.values())
        if not all_plans:
            return {"status": "no_plans"}
        return {"total_plans": len(all_plans), "total_tasks": sum(len(p.tasks) for p in all_plans)}