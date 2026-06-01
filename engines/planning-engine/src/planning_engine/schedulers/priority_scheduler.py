"""Priority Scheduler — Schedule tasks based on priority scoring"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from enum import Enum
import uuid


class PriorityLevel(Enum):
    P0_CRITICAL = 0
    P1_HIGH = 1
    P2_MEDIUM = 2
    P3_LOW = 3
    P4_BACKLOG = 4


@dataclass
class PriorityTask:
    id: str = field(default_factory=lambda: f"PT-{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    priority: PriorityLevel = PriorityLevel.P2_MEDIUM
    weight: float = 1.0
    urgency: float = 0.5  # 0-1 time pressure
    importance: float = 0.5  # 0-1 value
    effort: float = 1.0  # estimated hours
    dependencies: list[str] = field(default_factory=list)
    deadline: Optional[str] = None
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def priority_score(self) -> float:
        base = (1 - self.priority.value / 4) * 100
        urgency_bonus = self.urgency * 30
        importance_bonus = self.importance * 40
        effort_penalty = min(20, self.effort * 2)
        return base + urgency_bonus + importance_bonus - effort_penalty

    @property
    def is_overdue(self) -> bool:
        if not self.deadline:
            return False
        return datetime.fromisoformat(self.deadline) < datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority.name,
            "priority_score": round(self.priority_score, 1),
            "urgency": self.urgency,
            "importance": self.importance,
            "effort": self.effort,
            "deadline": self.deadline,
            "status": self.status,
        }


class PriorityScheduler:
    """Schedule and order tasks by composite priority score."""

    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.tasks: dict[str, PriorityTask] = {}
        self.completed: list[dict] = []

    def add_task(self, task: PriorityTask) -> PriorityTask:
        self.tasks[task.id] = task
        return task

    def remove_task(self, task_id: str) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False

    def get_sorted_queue(self) -> list[PriorityTask]:
        pending = [t for t in self.tasks.values() if t.status == "pending"]
        return sorted(pending, key=lambda t: t.priority_score, reverse=True)

    def get_next_tasks(self, count: int = None) -> list[PriorityTask]:
        count = count or self.max_concurrent
        queue = self.get_sorted_queue()
        ready = []
        for task in queue:
            if len(ready) >= count:
                break
            if self._deps_met(task):
                ready.append(task)
        return ready

    def start_task(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task or task.status != "pending":
            return False
        if not self._deps_met(task):
            return False
        running = sum(1 for t in self.tasks.values() if t.status == "running")
        if running >= self.max_concurrent:
            return False
        task.status = "running"
        return True

    def complete_task(self, task_id: str, success: bool = True) -> bool:
        task = self.tasks.get(task_id)
        if not task or task.status != "running":
            return False
        task.status = "completed" if success else "failed"
        self.completed.append(task.to_dict())
        return True

    def recalculate_priorities(self):
        for task in self.tasks.values():
            if task.is_overdue:
                task.urgency = min(1.0, task.urgency + 0.3)
                task.priority = PriorityLevel(max(0, task.priority.value - 1))

    def get_priority_distribution(self) -> dict:
        dist = {level.name: 0 for level in PriorityLevel}
        for task in self.tasks.values():
            if task.status == "pending":
                dist[task.priority.name] += 1
        return dist

    def get_schedule_summary(self) -> dict:
        total = len(self.tasks)
        pending = sum(1 for t in self.tasks.values() if t.status == "pending")
        running = sum(1 for t in self.tasks.values() if t.status == "running")
        completed = sum(1 for t in self.tasks.values() if t.status == "completed")
        failed = sum(1 for t in self.tasks.values() if t.status == "failed")
        return {
            "total_tasks": total,
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "priority_distribution": self.get_priority_distribution(),
            "avg_score": round(
                sum(t.priority_score for t in self.tasks.values() if t.status == "pending")
                / max(1, pending), 1
            ),
        }

    def _deps_met(self, task: PriorityTask) -> bool:
        for dep_id in task.dependencies:
            dep = self.tasks.get(dep_id)
            if not dep or dep.status != "completed":
                return False
        return True

    def to_dict(self) -> dict:
        return {
            "max_concurrent": self.max_concurrent,
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "summary": self.get_schedule_summary(),
        }
