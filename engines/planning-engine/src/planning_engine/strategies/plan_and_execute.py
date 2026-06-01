"""Plan and Execute — Classic two-phase planning strategy"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable
import uuid


@dataclass
class PlanStep:
    id: str = field(default_factory=lambda: f"PS-{uuid.uuid4().hex[:8]}")
    action: str = ""
    description: str = ""
    expected_outcome: str = ""
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"
    result: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action": self.action,
            "description": self.description,
            "expected_outcome": self.expected_outcome,
            "dependencies": self.dependencies,
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class Plan:
    id: str = field(default_factory=lambda: f"PLAN-{uuid.uuid4().hex[:8]}")
    goal: str = ""
    steps: list[PlanStep] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "draft"
    context: dict = field(default_factory=dict)

    @property
    def progress(self) -> float:
        if not self.steps:
            return 0.0
        done = sum(1 for s in self.steps if s.status == "completed")
        return done / len(self.steps) * 100

    @property
    def is_complete(self) -> bool:
        return all(s.status in ("completed", "skipped") for s in self.steps)

    @property
    def has_failures(self) -> bool:
        return any(s.status == "failed" for s in self.steps)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "steps": [s.to_dict() for s in self.steps],
            "progress": f"{self.progress:.1f}%",
            "status": self.status,
            "created_at": self.created_at,
        }


class PlanAndExecute:
    """Two-phase strategy: plan thoroughly, then execute step by step."""

    def __init__(self, planner_fn: Optional[Callable] = None,
                 executor_fn: Optional[Callable] = None):
        self.planner_fn = planner_fn or self._default_planner
        self.executor_fn = executor_fn or self._default_executor
        self.plans: dict[str, Plan] = {}
        self.execution_log: list[dict] = []

    def plan(self, goal: str, context: dict = None) -> Plan:
        plan = self.planner_fn(goal, context or {})
        plan.goal = goal
        plan.context = context or {}
        plan.status = "ready"
        self.plans[plan.id] = plan
        return plan

    def execute(self, plan_id: str) -> Plan:
        plan = self.plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        plan.status = "executing"
        for step in plan.steps:
            if step.status != "pending":
                continue
            if not self._deps_satisfied(plan, step):
                step.status = "blocked"
                continue
            result = self._execute_step(plan, step)
            self.execution_log.append({
                "plan_id": plan_id,
                "step_id": step.id,
                "action": step.action,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            if result["success"]:
                step.status = "completed"
                step.result = result.get("output", "")
            else:
                if step.retry_count < step.max_retries:
                    step.retry_count += 1
                    step.status = "pending"
                else:
                    step.status = "failed"
                    step.error = result.get("error", "unknown")
                    plan.status = "failed"
                    return plan
        plan.status = "completed" if plan.is_complete else "partial"
        return plan

    def replan(self, plan_id: str, reason: str) -> Plan:
        old_plan = self.plans.get(plan_id)
        if not old_plan:
            raise ValueError(f"Plan {plan_id} not found")
        failed_steps = [s for s in old_plan.steps if s.status == "failed"]
        new_plan = self.planner_fn(old_plan.goal, {
            **old_plan.context,
            "failed_steps": [s.to_dict() for s in failed_steps],
            "replan_reason": reason,
        })
        new_plan.goal = old_plan.goal
        new_plan.context = old_plan.context
        new_plan.status = "ready"
        self.plans[new_plan.id] = new_plan
        return new_plan

    def get_next_step(self, plan_id: str) -> Optional[PlanStep]:
        plan = self.plans.get(plan_id)
        if not plan:
            return None
        for step in plan.steps:
            if step.status == "pending" and self._deps_satisfied(plan, step):
                return step
        return None

    def get_plan_summary(self, plan_id: str) -> dict:
        plan = self.plans.get(plan_id)
        if not plan:
            return {"error": "plan not found"}
        return {
            "id": plan.id,
            "goal": plan.goal,
            "status": plan.status,
            "progress": f"{plan.progress:.1f}%",
            "total_steps": len(plan.steps),
            "completed": sum(1 for s in plan.steps if s.status == "completed"),
            "failed": sum(1 for s in plan.steps if s.status == "failed"),
            "pending": sum(1 for s in plan.steps if s.status == "pending"),
        }

    def _deps_satisfied(self, plan: Plan, step: PlanStep) -> bool:
        step_ids = {s.id for s in plan.steps}
        for dep_id in step.dependencies:
            if dep_id in step_ids:
                dep_step = next(s for s in plan.steps if s.id == dep_id)
                if dep_step.status != "completed":
                    return False
        return True

    def _execute_step(self, plan: Plan, step: PlanStep) -> dict:
        try:
            output = self.executor_fn(step, plan.context)
            return {"success": True, "output": str(output)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _default_planner(goal: str, context: dict) -> Plan:
        plan = Plan(goal=goal, context=context)
        phases = [
            ("research", "Research the problem domain", "Understand requirements"),
            ("design", "Design the solution approach", "Architecture defined"),
            ("implement", "Implement the solution", "Code working"),
            ("test", "Test and verify", "Tests passing"),
            ("review", "Final review and polish", "Ready for delivery"),
        ]
        prev_id = None
        for action, desc, outcome in phases:
            step = PlanStep(
                action=action,
                description=desc,
                expected_outcome=outcome,
                dependencies=[prev_id] if prev_id else [],
            )
            plan.steps.append(step)
            prev_id = step.id
        return plan

    @staticmethod
    def _default_executor(step: PlanStep, context: dict) -> str:
        return f"Executed: {step.action} - {step.description}"
