"""Recovery Planner — Generate recovery plans after failures"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RecoveryPlan:
    failure_id: str
    strategy: str
    steps: list[str] = field(default_factory=list)
    estimated_recovery_time: str = ""
    confidence: float = 0.5
    rollback_required: bool = False


class RecoveryPlanner:
    """Generate recovery plans for detected failures."""

    STRATEGIES = {
        "retry": "Retry the failed operation",
        "reassign": "Reassign to a different agent",
        "descope": "Reduce scope to essential features",
        "rollback": "Revert to last known good state",
        "escalate": "Escalate to human operator",
        "parallelize": "Split into parallel smaller tasks",
    }

    def create_recovery_plan(self, failure_type: str, affected_tasks: list[str]) -> RecoveryPlan:
        if failure_type == "task_failed":
            return RecoveryPlan(
                failure_id=failure_type,
                strategy="retry",
                steps=["Analyze failure cause", "Fix root cause", "Retry task", "Verify result"],
                estimated_recovery_time="2-4 hours",
                confidence=0.7,
            )
        elif failure_type == "deadline_miss":
            return RecoveryPlan(
                failure_id=failure_type,
                strategy="descope",
                steps=["Identify critical path", "Remove non-essential tasks", "Focus resources", "Re-baseline timeline"],
                estimated_recovery_time="1-2 days",
                confidence=0.6,
            )
        elif failure_type == "safety_violation":
            return RecoveryPlan(
                failure_id=failure_type,
                strategy="rollback",
                steps=["Halt execution", "Assess damage", "Rollback to checkpoint", "Review safety policies"],
                estimated_recovery_time="4-8 hours",
                confidence=0.9,
                rollback_required=True,
            )
        else:
            return RecoveryPlan(
                failure_id=failure_type,
                strategy="escalate",
                steps=["Document failure", "Escalate to human", "Await decision"],
                estimated_recovery_time="unknown",
                confidence=0.5,
            )
