"""Deadline Manager — Track and enforce deadlines"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Deadline:
    task_id: str
    deadline: str  # ISO timestamp
    warning_days: int = 3
    missed: bool = False


class DeadlineManager:
    """Track and warn about approaching deadlines."""

    def __init__(self):
        self.deadlines: dict[str, Deadline] = {}

    def set_deadline(self, task_id: str, deadline: str, warning_days: int = 3):
        self.deadlines[task_id] = Deadline(task_id=task_id, deadline=deadline, warning_days=warning_days)

    def get_approaching(self) -> list[Deadline]:
        now = datetime.now(timezone.utc)
        approaching = []
        for dl in self.deadlines.values():
            deadline_dt = datetime.fromisoformat(dl.deadline.replace("Z", "+00:00"))
            days_left = (deadline_dt - now).days
            if 0 <= days_left <= dl.warning_days:
                approaching.append(dl)
        return approaching

    def get_overdue(self) -> list[Deadline]:
        now = datetime.now(timezone.utc)
        overdue = []
        for dl in self.deadlines.values():
            deadline_dt = datetime.fromisoformat(dl.deadline.replace("Z", "+00:00"))
            if deadline_dt < now:
                dl.missed = True
                overdue.append(dl)
        return overdue
