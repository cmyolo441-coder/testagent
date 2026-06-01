"""Replanning Engine — Adaptive replanning on failure or change"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime, timezone


class ReplanTrigger(Enum):
    TASK_FAILED = "task_failed"
    DEADLINE_MISS = "deadline_miss"
    BUDGET_EXCEEDED = "budget_exceeded"
    SCOPE_CHANGE = "scope_change"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    RISK_OCCURRED = "risk_occurred"


@dataclass
class ReplanDecision:
    trigger: ReplanTrigger
    affected_tasks: list[str]
    strategy: str
    changes: list[dict]
    confidence: float
    rationale: str


class ReplanningEngine:
    """Decides when and how to replan based on mission state."""

    STRATEGIES = {
        "reschedule": "Move tasks to later dates",
        "reassign": "Assign to different agents",
        "descope": "Remove non-critical tasks",
        "parallelize": "Run tasks in parallel",
        "escalate": "Request human intervention",
        "rollback": "Revert to last checkpoint",
        "accept": "Accept delay and continue",
    }

    def analyze_and_replan(self, trigger: ReplanTrigger, mission_state: dict) -> ReplanDecision:
        failed_tasks = mission_state.get("failed_tasks", [])
        total_tasks = mission_state.get("total_tasks", 0)
        progress = mission_state.get("progress", 0)
        elapsed_ratio = mission_state.get("elapsed_ratio", 0)

        if trigger == ReplanTrigger.TASK_FAILED:
            return self._handle_task_failure(failed_tasks, total_tasks, progress, elapsed_ratio)
        elif trigger == ReplanTrigger.DEADLINE_MISS:
            return self._handle_deadline_miss(progress, elapsed_ratio, total_tasks)
        elif trigger == ReplanTrigger.SCOPE_CHANGE:
            return self._handle_scope_change(mission_state)
        else:
            return ReplanDecision(
                trigger=trigger,
                affected_tasks=[],
                strategy="accept",
                changes=[],
                confidence=0.5,
                rationale=f"Default handling for trigger: {trigger.value}",
            )

    def _handle_task_failure(self, failed, total, progress, elapsed) -> ReplanDecision:
        failure_rate = len(failed) / total if total > 0 else 0
        if failure_rate > 0.3:
            strategy = "escalate"
            rationale = f"High failure rate ({failure_rate:.0%}) — human review needed"
            confidence = 0.9
        elif failure_rate > 0.1:
            strategy = "reassign"
            rationale = f"Moderate failures — reassigning tasks to different agents"
            confidence = 0.7
        else:
            strategy = "reschedule"
            rationale = "Minor failures — rescheduling failed tasks"
            confidence = 0.8

        return ReplanDecision(
            trigger=ReplanTrigger.TASK_FAILED,
            affected_tasks=failed,
            strategy=strategy,
            changes=[{"action": strategy, "tasks": failed}],
            confidence=confidence,
            rationale=rationale,
        )

    def _handle_deadline_miss(self, progress, elapsed, total) -> ReplanDecision:
        if elapsed > 0.5 and progress < 30:
            strategy = "descope"
            rationale = "Behind schedule — descoping non-critical tasks"
        elif elapsed > 0.8 and progress < 70:
            strategy = "escalate"
            rationale = "Critical delay — escalation required"
        else:
            strategy = "parallelize"
            rationale = "Moderate delay — increasing parallelism"

        return ReplanDecision(
            trigger=ReplanTrigger.DEADLINE_MISS,
            affected_tasks=[],
            strategy=strategy,
            changes=[{"action": strategy}],
            confidence=0.7,
            rationale=rationale,
        )

    def _handle_scope_change(self, state) -> ReplanDecision:
        return ReplanDecision(
            trigger=ReplanTrigger.SCOPE_CHANGE,
            affected_tasks=[],
            strategy="reschedule",
            changes=[{"action": "rebuild_objective_tree"}],
            confidence=0.6,
            rationale="Scope changed — rebuilding objective tree and milestones",
        )
