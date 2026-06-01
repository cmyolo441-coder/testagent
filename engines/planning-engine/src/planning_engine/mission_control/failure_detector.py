"""Failure Detector — Detect and classify task/mission failures"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FailureType(Enum):
    TASK_FAILED = "task_failed"
    DEADLINE_MISS = "deadline_miss"
    BUDGET_EXCEED = "budget_exceed"
    QUALITY_FAIL = "quality_fail"
    DEPENDENCY_FAIL = "dependency_fail"
    RESOURCE_UNAVAIL = "resource_unavailable"
    SAFETY_VIOLATION = "safety_violation"


@dataclass
class Failure:
    failure_type: FailureType
    description: str
    severity: str = "medium"  # low, medium, high, critical
    affected_tasks: list[str] = None
    recovery_suggestion: str = ""

    def __post_init__(self):
        if self.affected_tasks is None:
            self.affected_tasks = []


class FailureDetector:
    """Detect and classify failures in mission execution."""

    def __init__(self):
        self.failures: list[Failure] = []

    def detect(self, tasks: list[dict], mission: dict) -> list[Failure]:
        failures = []

        # Check for failed tasks
        for task in tasks:
            if task.get("status") == "failed":
                failures.append(Failure(
                    failure_type=FailureType.TASK_FAILED,
                    description=f"Task failed: {task.get('title', task.get('id', '?'))}",
                    severity="high",
                    affected_tasks=[task.get("id", "")],
                    recovery_suggestion="Retry or reassign task",
                ))

        # Check for overdue tasks (simple heuristic)
        for task in tasks:
            if task.get("status") == "pending" and task.get("priority") == "critical":
                failures.append(Failure(
                    failure_type=FailureType.DEADLINE_MISS,
                    description=f"Critical task still pending: {task.get('title', '?')}",
                    severity="medium",
                    affected_tasks=[task.get("id", "")],
                    recovery_suggestion="Escalate or reprioritize",
                ))

        self.failures.extend(failures)
        return failures

    def get_summary(self) -> dict:
        by_type = {}
        for f in self.failures:
            by_type[f.failure_type.value] = by_type.get(f.failure_type.value, 0) + 1
        return {
            "total_failures": len(self.failures),
            "by_type": by_type,
            "critical": sum(1 for f in self.failures if f.severity == "critical"),
        }
