"""Labor Allocator — Priority task queue with skill-aware assignment."""
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
import heapq
import itertools
import time
import uuid


@dataclass
class Task:
    id: str = field(default_factory=lambda: f"TASK-{uuid.uuid4().hex[:8]}")
    title: str = ""
    required_skills: list[str] = field(default_factory=list)
    priority: int = 5  # lower = more urgent
    payload: Any = None
    assigned_to: Optional[str] = None
    status: str = "queued"  # queued | assigned | done | failed
    created_at: float = field(default_factory=time.time)


class LaborAllocator:
    """Distribute tasks to agents based on skill match and current load."""

    def __init__(self, society=None, registry=None, max_load: int = 5):
        self.society = society
        self.registry = registry
        self.max_load = max_load
        self.queue: list[tuple[int, int, Task]] = []  # heap of (priority, seq, task)
        self._seq = itertools.count()
        self.tasks: dict[str, Task] = {}
        self.load: dict[str, int] = {}  # agent_id -> in-flight task count

    def submit(self, task: Task) -> Task:
        self.tasks[task.id] = task
        heapq.heappush(self.queue, (task.priority, next(self._seq), task))
        return task

    def _candidate_agents(self, required_skills: list[str]) -> list[tuple[str, list[str]]]:
        """Return [(agent_id, skills)] from society or registry."""
        out: list[tuple[str, list[str]]] = []
        if self.society is not None and getattr(self.society, "members", None):
            for m in self.society.members.values():
                if getattr(m, "active", True):
                    out.append((m.id, list(getattr(m, "skills", []) or [])))
        if self.registry is not None and getattr(self.registry, "specialists", None):
            for spec in self.registry.specialists.values():
                out.append((spec.id, list(getattr(spec, "skills", []) or [])))
        return out

    def _score(self, agent_id: str, agent_skills: list[str], required: list[str]) -> float:
        if not required:
            match = 1.0
        else:
            hits = sum(1 for s in required if s in agent_skills)
            match = hits / len(required)
        load = self.load.get(agent_id, 0)
        if load >= self.max_load:
            return -1.0
        load_factor = 1.0 - (load / max(self.max_load, 1))
        return match * 0.7 + load_factor * 0.3

    def assign_task(self, task: Task) -> Optional[str]:
        candidates = self._candidate_agents(task.required_skills)
        best_id: Optional[str] = None
        best_score = -1.0
        for agent_id, skills in candidates:
            score = self._score(agent_id, skills, task.required_skills)
            if score > best_score:
                best_score = score
                best_id = agent_id
        if best_id is None or best_score < 0:
            return None
        task.assigned_to = best_id
        task.status = "assigned"
        self.load[best_id] = self.load.get(best_id, 0) + 1
        return best_id

    def drain(self) -> list[Task]:
        """Pop tasks in priority order and assign each. Returns assigned tasks."""
        assigned: list[Task] = []
        leftovers: list[tuple[int, int, Task]] = []
        while self.queue:
            priority, seq, task = heapq.heappop(self.queue)
            if task.status != "queued":
                continue
            who = self.assign_task(task)
            if who is None:
                leftovers.append((priority, seq, task))
            else:
                assigned.append(task)
        for item in leftovers:
            heapq.heappush(self.queue, item)
        return assigned

    def complete(self, task_id: str, success: bool = True) -> None:
        task = self.tasks.get(task_id)
        if not task or task.assigned_to is None:
            return
        self.load[task.assigned_to] = max(0, self.load.get(task.assigned_to, 0) - 1)
        task.status = "done" if success else "failed"

    def rebalance(self) -> dict[str, int]:
        """Reset queued-but-unassignable tasks and recompute load summary."""
        for t in self.tasks.values():
            if t.status == "assigned" and t.assigned_to and self.load.get(t.assigned_to, 0) > self.max_load:
                t.assigned_to = None
                t.status = "queued"
                heapq.heappush(self.queue, (t.priority, next(self._seq), t))
        return dict(self.load)

    def stats(self) -> dict:
        statuses: dict[str, int] = {}
        for t in self.tasks.values():
            statuses[t.status] = statuses.get(t.status, 0) + 1
        return {"tasks": len(self.tasks), "by_status": statuses, "load": dict(self.load)}
