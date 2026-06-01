"""PlanExecuteLoop — Plan first, then execute step-by-step honoring deps."""
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from datetime import datetime, timezone


@dataclass
class PlanStep:
    id: str
    description: str
    tool: str = ""
    args: dict = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"  # pending | running | done | failed | skipped
    result: Any = None
    verification: str = ""
    attempts: int = 0


@dataclass
class PlanExecRecord:
    iteration: int
    step_id: str
    description: str
    status: str
    result: Any = None
    verification: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class PlanExecuteLoop:
    """Build a plan, then execute steps in dependency order with verify+replan."""

    def __init__(self, max_replans: int = 3, max_step_attempts: int = 2):
        self.max_replans = max_replans
        self.max_step_attempts = max_step_attempts
        self.plan: list[PlanStep] = []
        self.step_results: dict[str, Any] = {}
        self.records: list[PlanExecRecord] = []
        self._plan_fn: Optional[Callable] = None
        self._exec_fn: Optional[Callable] = None
        self._verify_fn: Optional[Callable] = None
        self._replan_fn: Optional[Callable] = None

    def set_plan(self, fn: Callable):
        self._plan_fn = fn

    def set_exec(self, fn: Callable):
        self._exec_fn = fn

    def set_verify(self, fn: Callable):
        self._verify_fn = fn

    def set_replan(self, fn: Callable):
        self._replan_fn = fn

    @staticmethod
    def _coerce_plan(raw) -> list[PlanStep]:
        out: list[PlanStep] = []
        for idx, p in enumerate(raw or []):
            if isinstance(p, PlanStep):
                out.append(p)
            elif isinstance(p, dict):
                out.append(PlanStep(
                    id=str(p.get("id", f"s{idx}")),
                    description=p.get("description", ""),
                    tool=p.get("tool", ""),
                    args=p.get("args", {}) or {},
                    depends_on=list(p.get("depends_on", []) or []),
                ))
        return out

    def _deps_satisfied(self, step: PlanStep) -> bool:
        for dep in step.depends_on:
            done = next((s for s in self.plan if s.id == dep), None)
            if done is None or done.status != "done":
                return False
        return True

    def _next_runnable(self) -> Optional[PlanStep]:
        for s in self.plan:
            if s.status == "pending" and self._deps_satisfied(s):
                return s
        return None

    def run(self, initial_context: dict = None) -> list[PlanExecRecord]:
        context = dict(initial_context or {})
        if not self._plan_fn:
            return self.records

        self.plan = self._coerce_plan(self._plan_fn(context))
        context["plan"] = self.plan
        context["step_results"] = self.step_results

        replans = 0
        iteration = 0
        # Cap total iterations to avoid infinite loops on malformed deps
        max_total = max(1, len(self.plan) * (self.max_step_attempts + 1) + self.max_replans + 5)

        while iteration < max_total:
            step = self._next_runnable()
            if step is None:
                # nothing runnable — either done or stuck on deps
                pending = [s for s in self.plan if s.status == "pending"]
                if not pending:
                    break
                # stuck — try replan
                if self._replan_fn and replans < self.max_replans:
                    replans += 1
                    new_plan = self._coerce_plan(
                        self._replan_fn(context, self.plan, reason="deps_unsatisfiable")
                    )
                    if new_plan:
                        self.plan = new_plan
                        context["plan"] = self.plan
                        continue
                # give up
                for s in pending:
                    s.status = "skipped"
                    self.records.append(PlanExecRecord(
                        iteration=iteration, step_id=s.id,
                        description=s.description, status="skipped",
                    ))
                break

            iteration += 1
            step.status = "running"
            step.attempts += 1
            try:
                if self._exec_fn:
                    step.result = self._exec_fn(context, step)
                self.step_results[step.id] = step.result
                context["step_results"] = self.step_results
                context["last_step_result"] = step.result
            except Exception as e:
                step.result = {"error": str(e)}
                step.status = "failed"
                self.records.append(PlanExecRecord(
                    iteration=iteration, step_id=step.id,
                    description=step.description, status="failed",
                    result=step.result,
                ))
                if step.attempts < self.max_step_attempts:
                    step.status = "pending"
                    continue
                # trigger replan
                if self._replan_fn and replans < self.max_replans:
                    replans += 1
                    new_plan = self._coerce_plan(
                        self._replan_fn(context, self.plan, reason=f"exec_failed:{step.id}")
                    )
                    if new_plan:
                        self.plan = new_plan
                        context["plan"] = self.plan
                continue

            # VERIFY
            ok = True
            if self._verify_fn:
                v = self._verify_fn(context, step)
                if isinstance(v, dict):
                    step.verification = str(v.get("reason", ""))
                    ok = bool(v.get("ok", True))
                elif isinstance(v, bool):
                    ok = v
                else:
                    step.verification = str(v) if v is not None else ""

            if ok:
                step.status = "done"
                self.records.append(PlanExecRecord(
                    iteration=iteration, step_id=step.id,
                    description=step.description, status="done",
                    result=step.result, verification=step.verification,
                ))
            else:
                step.status = "failed"
                self.records.append(PlanExecRecord(
                    iteration=iteration, step_id=step.id,
                    description=step.description, status="failed",
                    result=step.result, verification=step.verification,
                ))
                if step.attempts < self.max_step_attempts:
                    step.status = "pending"
                    continue
                if self._replan_fn and replans < self.max_replans:
                    replans += 1
                    new_plan = self._coerce_plan(
                        self._replan_fn(context, self.plan, reason=f"verify_failed:{step.id}")
                    )
                    if new_plan:
                        self.plan = new_plan
                        context["plan"] = self.plan

        return self.records

    def get_summary(self) -> dict:
        return {
            "plan_size": len(self.plan),
            "done": sum(1 for s in self.plan if s.status == "done"),
            "failed": sum(1 for s in self.plan if s.status == "failed"),
            "skipped": sum(1 for s in self.plan if s.status == "skipped"),
            "iterations": len(self.records),
        }
