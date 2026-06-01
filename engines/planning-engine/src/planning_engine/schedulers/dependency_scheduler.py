"""Dependency Scheduler — Schedule tasks respecting dependency constraints"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict
import uuid


@dataclass
class DepTask:
    id: str = field(default_factory=lambda: f"DT-{uuid.uuid4().hex[:8]}")
    title: str = ""
    duration: int = 1  # hours
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"
    earliest_start: int = 0  # hours from project start
    earliest_finish: int = 0
    latest_start: int = 0
    latest_finish: int = 0
    slack: int = 0
    assigned_agent: Optional[str] = None

    @property
    def is_critical(self) -> bool:
        return self.slack == 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "duration": self.duration,
            "dependencies": self.dependencies,
            "status": self.status,
            "earliest_start": self.earliest_start,
            "earliest_finish": self.earliest_finish,
            "latest_start": self.latest_start,
            "latest_finish": self.latest_finish,
            "slack": self.slack,
            "is_critical": self.is_critical,
        }


class DependencyScheduler:
    """Schedule tasks with full dependency graph analysis and critical path."""

    def __init__(self):
        self.tasks: dict[str, DepTask] = {}
        self._adj: dict[str, list[str]] = defaultdict(list)
        self._reverse_adj: dict[str, list[str]] = defaultdict(list)

    def add_task(self, task: DepTask) -> DepTask:
        self.tasks[task.id] = task
        for dep_id in task.dependencies:
            self._adj[dep_id].append(task.id)
            self._reverse_adj[task.id].append(dep_id)
        return task

    def remove_task(self, task_id: str) -> bool:
        if task_id not in self.tasks:
            return False
        for dep_id in self._reverse_adj.get(task_id, []):
            self.tasks[dep_id].dependencies.remove(task_id)
        for dep_id in self.tasks.get(task_id, DepTask()).dependencies:
            if task_id in self._adj.get(dep_id, []):
                self._adj[dep_id].remove(task_id)
        del self.tasks[task_id]
        return True

    def has_cycle(self) -> bool:
        visited = set()
        rec_stack = set()

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in self._adj.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.discard(node)
            return False

        for node in self.tasks:
            if node not in visited:
                if dfs(node):
                    return True
        return False

    def topological_sort(self) -> list[str]:
        visited = set()
        order = []

        def dfs(node):
            visited.add(node)
            for neighbor in self._adj.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
            order.append(node)

        for node in self.tasks:
            if node not in visited:
                dfs(node)
        return list(reversed(order))

    def calculate_schedule(self) -> dict:
        topo = self.topological_sort()
        # Forward pass
        for node in topo:
            task = self.tasks[node]
            task.earliest_start = max(
                (self.tasks[dep].earliest_finish for dep in task.dependencies),
                default=0
            )
            task.earliest_finish = task.earliest_start + task.duration

        project_end = max(
            (t.earliest_finish for t in self.tasks.values()),
            default=0
        )

        # Backward pass
        for node in reversed(topo):
            task = self.tasks[node]
            successors = self._adj.get(node, [])
            if not successors:
                task.latest_finish = project_end
            else:
                task.latest_finish = min(
                    self.tasks[s].latest_start for s in successors
                )
            task.latest_start = task.latest_finish - task.duration
            task.slack = task.latest_start - task.earliest_start

        return {
            "project_duration": project_end,
            "critical_path": [t.id for t in self.tasks.values() if t.is_critical],
            "total_tasks": len(self.tasks),
        }

    def get_critical_path(self) -> list[str]:
        self.calculate_schedule()
        return [t.id for t in self.tasks.values() if t.is_critical]

    def get_ready_tasks(self) -> list[DepTask]:
        ready = []
        for task in self.tasks.values():
            if task.status == "pending":
                deps_done = all(
                    self.tasks.get(d, DepTask()).status == "completed"
                    for d in task.dependencies
                )
                if deps_done:
                    ready.append(task)
        return sorted(ready, key=lambda t: t.earliest_start)

    def assign_task(self, task_id: str, agent_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task or task.status != "pending":
            return False
        task.assigned_agent = agent_id
        task.status = "assigned"
        return True

    def start_task(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task or task.status != "assigned":
            return False
        task.status = "running"
        return True

    def complete_task(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task or task.status != "running":
            return False
        task.status = "completed"
        return True

    def get_schedule_summary(self) -> dict:
        schedule = self.calculate_schedule()
        by_status = defaultdict(int)
        for task in self.tasks.values():
            by_status[task.status] += 1
        return {
            **schedule,
            "by_status": dict(by_status),
            "total_slack": sum(t.slack for t in self.tasks.values()),
        }

    def to_dict(self) -> dict:
        return {
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "summary": self.get_schedule_summary(),
        }
