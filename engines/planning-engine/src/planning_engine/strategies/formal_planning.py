"""Formal Planning — Constraint-based formal verification of plans"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable
import uuid


@dataclass
class Constraint:
    id: str = field(default_factory=lambda: f"CON-{uuid.uuid4().hex[:8]}")
    name: str = ""
    constraint_type: str = "precondition"  # precondition, postcondition, invariant, temporal
    expression: str = ""
    scope: str = "global"  # global, step, resource
    is_satisfied: bool = True
    violation_message: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.constraint_type,
            "expression": self.expression,
            "scope": self.scope,
            "satisfied": self.is_satisfied,
            "violation": self.violation_message,
        }


@dataclass
class PlanAction:
    id: str = field(default_factory=lambda: f"ACT-{uuid.uuid4().hex[:8]}")
    name: str = ""
    preconditions: list[str] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)
    cost: float = 1.0
    duration: int = 1
    parameters: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "preconditions": self.preconditions,
            "effects": self.effects,
            "cost": self.cost,
            "duration": self.duration,
        }


@dataclass
class FormalPlan:
    id: str = field(default_factory=lambda: f"FP-{uuid.uuid4().hex[:8]}")
    goal: str = ""
    initial_state: list[str] = field(default_factory=list)
    actions: list[PlanAction] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    goal_state: list[str] = field(default_factory=list)
    is_valid: bool = False
    validation_errors: list[str] = field(default_factory=list)
    total_cost: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "initial_state": self.initial_state,
            "actions": [a.to_dict() for a in self.actions],
            "constraints": [c.to_dict() for c in self.constraints],
            "goal_state": self.goal_state,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
            "total_cost": self.total_cost,
        }


class FormalPlanning:
    """Constraint-based formal verification of action plans."""

    def __init__(self, state_validator: Optional[Callable] = None,
                 planner: Optional[Callable] = None):
        self.state_validator = state_validator or self._default_validator
        self.planner = planner or self._default_planner
        self.plans: dict[str, FormalPlan] = {}
        self.action_library: dict[str, PlanAction] = {}

    def create_plan(self, goal: str, initial_state: list[str] = None,
                    goal_state: list[str] = None) -> FormalPlan:
        plan = FormalPlan(
            goal=goal,
            initial_state=initial_state or [],
            goal_state=goal_state or [f"achieved({goal})"],
        )
        self.plans[plan.id] = plan
        return plan

    def add_action(self, plan_id: str, action: PlanAction) -> bool:
        plan = self.plans.get(plan_id)
        if not plan:
            return False
        plan.actions.append(action)
        return True

    def add_constraint(self, plan_id: str, constraint: Constraint) -> bool:
        plan = self.plans.get(plan_id)
        if not plan:
            return False
        plan.constraints.append(constraint)
        return True

    def validate_plan(self, plan_id: str) -> dict:
        plan = self.plans.get(plan_id)
        if not plan:
            return {"error": "plan not found"}
        errors = []
        # Validate preconditions
        state = set(plan.initial_state)
        for i, action in enumerate(plan.actions):
            for pre in action.preconditions:
                if pre not in state:
                    errors.append(f"Step {i}: precondition '{pre}' not met")
            for effect in action.effects:
                state.add(effect)
        # Validate goal achievement
        for goal in plan.goal_state:
            if goal not in state:
                errors.append(f"Goal '{goal}' not achievable")
        # Validate constraints
        for constraint in plan.constraints:
            is_satisfied = self._check_constraint(constraint, state, plan)
            constraint.is_satisfied = is_satisfied
            if not is_satisfied:
                errors.append(f"Constraint violated: {constraint.name}")
        plan.is_valid = len(errors) == 0
        plan.validation_errors = errors
        plan.total_cost = sum(a.cost for a in plan.actions)
        return {
            "plan_id": plan_id,
            "is_valid": plan.is_valid,
            "errors": errors,
            "total_cost": plan.total_cost,
            "action_count": len(plan.actions),
        }

    def generate_plan(self, problem: str, constraints: list[Constraint] = None) -> FormalPlan:
        plan = self.planner(problem, constraints or [])
        plan.goal = problem
        if constraints:
            plan.constraints = list(constraints)
        self.plans[plan.id] = plan
        self.validate_plan(plan.id)
        return plan

    def repair_plan(self, plan_id: str) -> FormalPlan:
        plan = self.plans.get(plan_id)
        if not plan or plan.is_valid:
            return plan
        # Try to fix by adding missing actions
        for error in plan.validation_errors:
            if "precondition" in error:
                # Find or create action that produces the missing precondition
                missing = error.split("'")[1]
                repair_action = self._find_repair_action(missing, plan)
                if repair_action:
                    plan.actions.insert(0, repair_action)
        self.validate_plan(plan_id)
        return plan

    def check_entailment(self, state: list[str], formula: str) -> bool:
        state_set = set(state)
        return formula in state_set

    def get_plan_metrics(self, plan_id: str) -> dict:
        plan = self.plans.get(plan_id)
        if not plan:
            return {"error": "plan not found"}
        return {
            "action_count": len(plan.actions),
            "constraint_count": len(plan.constraints),
            "total_cost": plan.total_cost,
            "is_valid": plan.is_valid,
            "error_count": len(plan.validation_errors),
            "unique_effects": len(set(
                e for a in plan.actions for e in a.effects
            )),
        }

    def export_pddl(self, plan_id: str) -> str:
        plan = self.plans.get(plan_id)
        if not plan:
            return ""
        lines = [f"; PDDL-like representation of plan: {plan.goal}"]
        lines.append("(:init")
        for s in plan.initial_state:
            lines.append(f"  ({s})")
        lines.append(")")
        lines.append("(:goal (and")
        for g in plan.goal_state:
            lines.append(f"  ({g})")
        lines.append("))")
        for action in plan.actions:
            lines.append(f"(:action {action.name}")
            lines.append(f"  :precondition (and")
            for p in action.preconditions:
                lines.append(f"    ({p})")
            lines.append(f"  )")
            lines.append(f"  :effect (and")
            for e in action.effects:
                lines.append(f"    ({e})")
            lines.append(f"  )")
            lines.append(")")
        return "\n".join(lines)

    def _check_constraint(self, constraint: Constraint, state: set, plan: FormalPlan) -> bool:
        if constraint.constraint_type == "invariant":
            return constraint.expression in state
        return True

    def _find_repair_action(self, missing_effect: str, plan: FormalPlan) -> Optional[PlanAction]:
        for action in self.action_library.values():
            if missing_effect in action.effects:
                return action
        return PlanAction(
            name=f"repair_{missing_effect}",
            effects=[missing_effect],
            cost=2.0,
        )

    @staticmethod
    def _default_validator(state: list[str], formula: str) -> bool:
        return formula in state

    @staticmethod
    def _default_planner(problem: str, constraints: list[Constraint]) -> FormalPlan:
        plan = FormalPlan(goal=problem)
        plan.actions = [
            PlanAction(
                name="analyze",
                preconditions=[],
                effects=["analyzed"],
                cost=1.0,
            ),
            PlanAction(
                name="implement",
                preconditions=["analyzed"],
                effects=["implemented"],
                cost=3.0,
            ),
            PlanAction(
                name="verify",
                preconditions=["implemented"],
                effects=[f"achieved({problem})"],
                cost=1.0,
            ),
        ]
        return plan
