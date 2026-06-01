"""Monthly Scheduler — Long-term monthly task planning and allocation"""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid


@dataclass
class MonthMilestone:
    id: str = field(default_factory=lambda: f"MM-{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    week: int = 1
    priority: str = "medium"
    status: str = "pending"
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "week": self.week,
            "priority": self.priority,
            "status": self.status,
            "dependencies": self.dependencies,
        }


@dataclass
class MonthPlan:
    year: int = 0
    month: int = 0
    milestones: list[MonthMilestone] = field(default_factory=list)
    total_capacity_hours: int = 160
    allocated_hours: int = 0
    themes: list[str] = field(default_factory=list)

    @property
    def utilization(self) -> float:
        return self.allocated_hours / self.total_capacity_hours if self.total_capacity_hours else 0

    @property
    def remaining_hours(self) -> int:
        return max(0, self.total_capacity_hours - self.allocated_hours)

    def to_dict(self) -> dict:
        return {
            "year": self.year,
            "month": self.month,
            "milestones": [m.to_dict() for m in self.milestones],
            "total_capacity_hours": self.total_capacity_hours,
            "allocated_hours": self.allocated_hours,
            "remaining_hours": self.remaining_hours,
            "utilization": f"{self.utilization:.0%}",
            "themes": self.themes,
            "milestone_count": len(self.milestones),
        }


class MonthlyScheduler:
    """Plan monthly work with milestones and capacity management."""

    MONTH_NAMES = [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    def __init__(self, working_hours_per_week: int = 40):
        self.hours_per_week = working_hours_per_week
        self.plans: dict[tuple[int, int], MonthPlan] = {}

    def create_plan(self, year: int, month: int, themes: list[str] = None) -> MonthPlan:
        weeks_in_month = self._weeks_in_month(year, month)
        plan = MonthPlan(
            year=year,
            month=month,
            total_capacity_hours=weeks_in_month * self.hours_per_week,
            themes=themes or [],
        )
        self.plans[(year, month)] = plan
        return plan

    def add_milestone(self, year: int, month: int, title: str, description: str = "",
                      week: int = 1, priority: str = "medium") -> MonthMilestone:
        plan = self.plans.get((year, month))
        if not plan:
            plan = self.create_plan(year, month)
        milestone = MonthMilestone(
            title=title, description=description, week=week, priority=priority
        )
        plan.milestones.append(milestone)
        return milestone

    def allocate_hours(self, year: int, month: int, hours: int) -> bool:
        plan = self.plans.get((year, month))
        if not plan:
            return False
        if plan.allocated_hours + hours > plan.total_capacity_hours:
            return False
        plan.allocated_hours += hours
        return True

    def get_weekly_breakdown(self, year: int, month: int) -> list[dict]:
        plan = self.plans.get((year, month))
        if not plan:
            return []
        weeks = []
        weeks_in_month = self._weeks_in_month(year, month)
        hours_per_week = plan.total_capacity_hours // weeks_in_month
        for w in range(1, weeks_in_month + 1):
            week_milestones = [m for m in plan.milestones if m.week == w]
            weeks.append({
                "week": w,
                "capacity_hours": hours_per_week,
                "milestones": [m.to_dict() for m in week_milestones],
                "milestone_count": len(week_milestones),
            })
        return weeks

    def get_overloaded_weeks(self, year: int, month: int) -> list[int]:
        plan = self.plans.get((year, month))
        if not plan:
            return []
        weeks_in_month = self._weeks_in_month(year, month)
        hours_per_week = plan.total_capacity_hours // weeks_in_month
        overloaded = []
        for w in range(1, weeks_in_month + 1):
            week_hours = sum(8 for m in plan.milestones if m.week == w)
            if week_hours > hours_per_week:
                overloaded.append(w)
        return overloaded

    def get_month_summary(self, year: int, month: int) -> dict:
        plan = self.plans.get((year, month))
        if not plan:
            return {"year": year, "month": month, "status": "no_plan"}
        by_priority = {}
        for m in plan.milestones:
            by_priority[m.priority] = by_priority.get(m.priority, 0) + 1
        return {
            "month_name": self.MONTH_NAMES[month],
            "year": year,
            "milestone_count": len(plan.milestones),
            "by_priority": by_priority,
            "capacity": f"{plan.allocated_hours}/{plan.total_capacity_hours}h",
            "utilization": f"{plan.utilization:.0%}",
            "themes": plan.themes,
        }

    def get_quarter_view(self, year: int, quarter: int) -> list[dict]:
        start_month = (quarter - 1) * 3 + 1
        return [self.get_month_summary(year, m) for m in range(start_month, start_month + 3)]

    @staticmethod
    def _weeks_in_month(year: int, month: int) -> int:
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        last_day = next_month - timedelta(days=1)
        return (last_day.day + 6) // 7
