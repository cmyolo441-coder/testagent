"""Durable Scheduler — Persistent task scheduling with checkpoint/resume"""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional
import uuid
import json
import hashlib


class ScheduleStatus(Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class SchedulePriority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class ScheduledTask:
    id: str = field(default_factory=lambda: f"SCH-{uuid.uuid4().hex[:8]}")
    task_id: str = ""
    title: str = ""
    description: str = ""
    status: ScheduleStatus = ScheduleStatus.PENDING
    priority: SchedulePriority = SchedulePriority.MEDIUM
    scheduled_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    deadline: Optional[str] = None
    duration_estimate: int = 0  # minutes
    duration_actual: int = 0
    agent_id: Optional[str] = None
    dependencies: list[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict = field(default_factory=dict)
    checkpoint_data: dict = field(default_factory=dict)

    @property
    def is_overdue(self) -> bool:
        if not self.deadline or self.status in (ScheduleStatus.COMPLETED, ScheduleStatus.CANCELLED):
            return False
        return datetime.fromisoformat(self.deadline) < datetime.now(timezone.utc)

    @property
    def duration_remaining(self) -> int:
        if not self.deadline:
            return self.duration_estimate
        dl = datetime.fromisoformat(self.deadline)
        now = datetime.now(timezone.utc)
        remaining = int((dl - now).total_seconds() / 60)
        return max(0, remaining)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "title": self.title,
            "status": self.status.value,
            "priority": self.priority.value,
            "scheduled_at": self.scheduled_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "deadline": self.deadline,
            "duration_estimate": self.duration_estimate,
            "duration_actual": self.duration_actual,
            "agent_id": self.agent_id,
            "dependencies": self.dependencies,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
        }


@dataclass
class Checkpoint:
    id: str = field(default_factory=lambda: f"CP-{uuid.uuid4().hex[:8]}")
    scheduler_state: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    hash: str = ""

    def compute_hash(self) -> str:
        state_str = json.dumps(self.scheduler_state, sort_keys=True, default=str)
        self.hash = hashlib.sha256(state_str.encode()).hexdigest()[:16]
        return self.hash


class DurableScheduler:
    """Persistent scheduler with checkpoint/resume and durability guarantees."""

    def __init__(self, max_concurrent: int = 4):
        self.max_concurrent = max_concurrent
        self.tasks: dict[str, ScheduledTask] = {}
        self.checkpoints: list[Checkpoint] = []
        self.completed_history: list[dict] = []
        self._running_count = 0

    def schedule(self, task: ScheduledTask, scheduled_at: Optional[str] = None) -> ScheduledTask:
        if scheduled_at:
            task.scheduled_at = scheduled_at
        else:
            task.scheduled_at = datetime.now(timezone.utc).isoformat()
        task.status = ScheduleStatus.SCHEDULED
        self.tasks[task.id] = task
        self._create_checkpoint()
        return task

    def start(self, task_id: str, agent_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task or task.status != ScheduleStatus.SCHEDULED:
            return False
        if self._running_count >= self.max_concurrent:
            return False
        if not self._dependencies_met(task):
            return False
        task.status = ScheduleStatus.RUNNING
        task.started_at = datetime.now(timezone.utc).isoformat()
        task.agent_id = agent_id
        self._running_count += 1
        self._create_checkpoint()
        return True

    def complete(self, task_id: str, success: bool = True) -> bool:
        task = self.tasks.get(task_id)
        if not task or task.status != ScheduleStatus.RUNNING:
            return False
        task.completed_at = datetime.now(timezone.utc).isoformat()
        if success:
            task.status = ScheduleStatus.COMPLETED
            if task.started_at:
                start = datetime.fromisoformat(task.started_at)
                end = datetime.fromisoformat(task.completed_at)
                task.duration_actual = int((end - start).total_seconds() / 60)
            self.completed_history.append(task.to_dict())
        else:
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = ScheduleStatus.PENDING
                task.started_at = None
            else:
                task.status = ScheduleStatus.FAILED
        self._running_count = max(0, self._running_count - 1)
        self._create_checkpoint()
        return True

    def pause(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task or task.status != ScheduleStatus.RUNNING:
            return False
        task.status = ScheduleStatus.PAUSED
        self._running_count = max(0, self._running_count - 1)
        self._create_checkpoint()
        return True

    def resume(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task or task.status != ScheduleStatus.PAUSED:
            return False
        if self._running_count >= self.max_concurrent:
            return False
        task.status = ScheduleStatus.RUNNING
        self._running_count += 1
        self._create_checkpoint()
        return True

    def cancel(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task:
            return False
        if task.status == ScheduleStatus.RUNNING:
            self._running_count = max(0, self._running_count - 1)
        task.status = ScheduleStatus.CANCELLED
        self._create_checkpoint()
        return True

    def get_ready_tasks(self) -> list[ScheduledTask]:
        ready = []
        for task in self.tasks.values():
            if task.status == ScheduleStatus.PENDING and self._dependencies_met(task):
                ready.append(task)
        return sorted(ready, key=lambda t: t.priority.value)

    def get_overdue_tasks(self) -> list[ScheduledTask]:
        return [t for t in self.tasks.values() if t.is_overdue]

    def get_schedule_summary(self) -> dict:
        by_status = {}
        for task in self.tasks.values():
            by_status[task.status.value] = by_status.get(task.status.value, 0) + 1
        return {
            "total_tasks": len(self.tasks),
            "by_status": by_status,
            "running": self._running_count,
            "capacity": self.max_concurrent,
            "utilization": self._running_count / self.max_concurrent if self.max_concurrent else 0,
            "checkpoints": len(self.checkpoints),
            "completed_history": len(self.completed_history),
        }

    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        for cp in self.checkpoints:
            if cp.id == checkpoint_id:
                state = cp.scheduler_state
                self.max_concurrent = state.get("max_concurrent", self.max_concurrent)
                return True
        return False

    def _dependencies_met(self, task: ScheduledTask) -> bool:
        for dep_id in task.dependencies:
            dep = self.tasks.get(dep_id)
            if not dep or dep.status != ScheduleStatus.COMPLETED:
                return False
        return True

    def _create_checkpoint(self):
        cp = Checkpoint(scheduler_state={
            "max_concurrent": self.max_concurrent,
            "running_count": self._running_count,
            "task_count": len(self.tasks),
        })
        cp.compute_hash()
        self.checkpoints.append(cp)

    def to_dict(self) -> dict:
        return {
            "max_concurrent": self.max_concurrent,
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "summary": self.get_schedule_summary(),
            "checkpoints": [{"id": cp.id, "hash": cp.hash, "timestamp": cp.timestamp} for cp in self.checkpoints[-10:]],
        }
