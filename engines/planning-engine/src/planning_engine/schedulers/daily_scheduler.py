"""Daily Scheduler — Schedule and manage daily task execution"""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid


@dataclass
class TimeBlock:
    id: str = field(default_factory=lambda: f"TB-{uuid.uuid4().hex[:8]}")
    start_hour: int = 9
    end_hour: int = 10
    task_id: Optional[str] = None
    task_title: str = ""
    category: str = "work"  # work, break, meeting, focus
    is_locked: bool = False

    @property
    def duration_minutes(self) -> int:
        return (self.end_hour - self.start_hour) * 60

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "start": f"{self.start_hour:02d}:00",
            "end": f"{self.end_hour:02d}:00",
            "duration_minutes": self.duration_minutes,
            "task_id": self.task_id,
            "task_title": self.task_title,
            "category": self.category,
            "is_locked": self.is_locked,
        }


@dataclass
class DailyPlan:
    date: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    blocks: list[TimeBlock] = field(default_factory=list)
    focus_hours: int = 4
    break_minutes: int = 60
    total_capacity_minutes: int = 480

    @property
    def utilized_minutes(self) -> int:
        return sum(b.duration_minutes for b in self.blocks if b.task_id)

    @property
    def utilization_ratio(self) -> float:
        return self.utilized_minutes / self.total_capacity_minutes if self.total_capacity_minutes else 0

    @property
    def free_blocks(self) -> list[TimeBlock]:
        return [b for b in self.blocks if not b.task_id]

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "blocks": [b.to_dict() for b in self.blocks],
            "utilized_minutes": self.utilized_minutes,
            "utilization": f"{self.utilization_ratio:.0%}",
            "total_blocks": len(self.blocks),
            "free_blocks": len(self.free_blocks),
        }


class DailyScheduler:
    """Create and manage daily schedules with time blocking."""

    def __init__(self, start_hour: int = 9, end_hour: int = 17, break_hour: int = 12):
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.break_hour = break_hour
        self.plans: dict[str, DailyPlan] = {}

    def create_plan(self, date: Optional[str] = None) -> DailyPlan:
        date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        plan = DailyPlan(date=date)
        for hour in range(self.start_hour, self.end_hour):
            if hour == self.break_hour:
                plan.blocks.append(TimeBlock(
                    start_hour=hour, end_hour=hour + 1, category="break"
                ))
            else:
                plan.blocks.append(TimeBlock(start_hour=hour, end_hour=hour + 1))
        self.plans[date] = plan
        return plan

    def assign_task(self, date: str, block_id: str, task_id: str, title: str) -> bool:
        plan = self.plans.get(date)
        if not plan:
            return False
        for block in plan.blocks:
            if block.id == block_id and not block.task_id and not block.is_locked:
                block.task_id = task_id
                block.task_title = title
                return True
        return False

    def assign_by_priority(self, date: str, tasks: list[dict]) -> list[dict]:
        plan = self.plans.get(date) or self.create_plan(date)
        assigned = []
        free = plan.free_blocks
        for task in tasks:
            if not free:
                break
            block = free.pop(0)
            block.task_id = task.get("id", "")
            block.task_title = task.get("title", "")
            assigned.append({"task": task, "block": block.to_dict()})
        return assigned

    def get_focus_blocks(self, date: str) -> list[TimeBlock]:
        plan = self.plans.get(date)
        if not plan:
            return []
        return [b for b in plan.blocks if b.category == "work" and not b.task_id]

    def get_day_summary(self, date: str) -> dict:
        plan = self.plans.get(date)
        if not plan:
            return {"date": date, "status": "no_plan"}
        return plan.to_dict()

    def get_week_overview(self, start_date: str) -> list[dict]:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        overview = []
        for i in range(5):
            day = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            overview.append(self.get_day_summary(day))
        return overview
