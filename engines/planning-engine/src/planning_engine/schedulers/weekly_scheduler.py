"""Weekly Scheduler — Plan and manage weekly task allocation"""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid


@dataclass
class WeeklySlot:
    id: str = field(default_factory=lambda: f"WS-{uuid.uuid4().hex[:8]}")
    day: str = "Monday"
    slot_index: int = 0
    start_hour: int = 9
    end_hour: int = 10
    task_id: Optional[str] = None
    task_title: str = ""
    category: str = "work"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "day": self.day,
            "slot": self.slot_index,
            "start": f"{self.start_hour:02d}:00",
            "end": f"{self.end_hour:02d}:00",
            "task_id": self.task_id,
            "task_title": self.task_title,
            "category": self.category,
        }


@dataclass
class DaySchedule:
    day_name: str
    slots: list[WeeklySlot] = field(default_factory=list)
    is_workday: bool = True

    @property
    def capacity_hours(self) -> int:
        return len([s for s in self.slots if s.category == "work"]) if self.is_workday else 0

    @property
    def utilized_hours(self) -> int:
        return len([s for s in self.slots if s.task_id and s.category == "work"])

    def to_dict(self) -> dict:
        return {
            "day": self.day_name,
            "is_workday": self.is_workday,
            "capacity_hours": self.capacity_hours,
            "utilized_hours": self.utilized_hours,
            "tasks": [s.to_dict() for s in self.slots if s.task_id],
        }


class WeeklyScheduler:
    """Create and manage weekly schedules with day-level granularity."""

    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    WEEKEND = ["Saturday", "Sunday"]

    def __init__(self, start_hour: int = 9, end_hour: int = 17, workdays: list[str] = None):
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.workdays = workdays or self.DAYS
        self.weeks: dict[str, dict[str, DaySchedule]] = {}

    def create_week(self, week_start: str) -> dict[str, DaySchedule]:
        start = datetime.strptime(week_start, "%Y-%m-%d")
        week = {}
        for i in range(7):
            day_date = start + timedelta(days=i)
            day_name = day_date.strftime("%A")
            is_workday = day_name in self.workdays
            day_schedule = DaySchedule(day_name=day_name, is_workday=is_workday)
            if is_workday:
                for hour in range(self.start_hour, self.end_hour):
                    day_schedule.slots.append(WeeklySlot(
                        day=day_name,
                        slot_index=hour - self.start_hour,
                        start_hour=hour,
                        end_hour=hour + 1,
                    ))
            week[day_name] = day_schedule
        self.weeks[week_start] = week
        return week

    def assign_task(self, week_start: str, day_name: str, slot_index: int,
                    task_id: str, title: str) -> bool:
        week = self.weeks.get(week_start)
        if not week:
            return False
        day = week.get(day_name)
        if not day:
            return False
        for slot in day.slots:
            if slot.slot_index == slot_index and not slot.task_id:
                slot.task_id = task_id
                slot.task_title = title
                return True
        return False

    def distribute_tasks(self, week_start: str, tasks: list[dict]) -> list[dict]:
        week = self.weeks.get(week_start) or self.create_week(week_start)
        assigned = []
        task_idx = 0
        for day_name in self.workdays:
            day = week.get(day_name)
            if not day:
                continue
            for slot in day.slots:
                if task_idx >= len(tasks):
                    break
                if not slot.task_id:
                    task = tasks[task_idx]
                    slot.task_id = task.get("id", "")
                    slot.task_title = task.get("title", "")
                    assigned.append({"task": task, "slot": slot.to_dict()})
                    task_idx += 1
        return assigned

    def get_bottleneck_days(self, week_start: str) -> list[str]:
        week = self.weeks.get(week_start)
        if not week:
            return []
        overloaded = []
        for day_name, day in week.items():
            if day.capacity_hours > 0 and day.utilized_hours > day.capacity_hours:
                overloaded.append(day_name)
        return overloaded

    def get_week_summary(self, week_start: str) -> dict:
        week = self.weeks.get(week_start)
        if not week:
            return {"week": week_start, "status": "no_plan"}
        total_capacity = sum(d.capacity_hours for d in week.values())
        total_utilized = sum(d.utilized_hours for d in week.values())
        total_tasks = sum(len([s for s in d.slots if s.task_id]) for d in week.values())
        return {
            "week_start": week_start,
            "total_capacity_hours": total_capacity,
            "utilized_hours": total_utilized,
            "utilization": f"{total_utilized / total_capacity:.0%}" if total_capacity else "0%",
            "total_tasks_scheduled": total_tasks,
            "days": {name: day.to_dict() for name, day in week.items()},
        }

    def get_remaining_capacity(self, week_start: str) -> dict[str, int]:
        week = self.weeks.get(week_start)
        if not week:
            return {}
        return {
            name: day.capacity_hours - day.utilized_hours
            for name, day in week.items()
            if day.is_workday
        }
