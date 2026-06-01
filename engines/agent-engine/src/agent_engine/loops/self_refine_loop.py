"""SelfRefineLoop — Generate → Critique → Refine until clean or max_iter."""
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from datetime import datetime, timezone


@dataclass
class Critique:
    issues: list[str] = field(default_factory=list)
    severity: str = "info"  # info | low | medium | high | critical
    notes: str = ""

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0


@dataclass
class RefineStep:
    iteration: int
    draft: Any = None
    critique: Optional[Critique] = None
    refined: Any = None
    accepted: bool = False
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class SelfRefineLoop:
    """Iterative self-refinement: gen → critique → refine."""

    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.steps: list[RefineStep] = []
        self.drafts: list[Any] = []
        self._gen_fn: Optional[Callable] = None
        self._critique_fn: Optional[Callable] = None
        self._refine_fn: Optional[Callable] = None
        self._accept_fn: Optional[Callable] = None

    def set_gen(self, fn: Callable):
        self._gen_fn = fn

    def set_critique(self, fn: Callable):
        self._critique_fn = fn

    def set_refine(self, fn: Callable):
        self._refine_fn = fn

    def set_accept(self, fn: Callable):
        """Optional override for acceptance check (default: critique.is_clean)."""
        self._accept_fn = fn

    @staticmethod
    def _coerce_critique(raw) -> Critique:
        if isinstance(raw, Critique):
            return raw
        if isinstance(raw, dict):
            return Critique(
                issues=list(raw.get("issues", []) or []),
                severity=str(raw.get("severity", "info")),
                notes=str(raw.get("notes", "")),
            )
        if isinstance(raw, (list, tuple)):
            return Critique(issues=list(raw))
        if raw is None:
            return Critique()
        return Critique(issues=[str(raw)])

    def run(self, initial_context: dict = None) -> list[RefineStep]:
        context = dict(initial_context or {})
        current_draft = context.get("initial_draft")

        for i in range(self.max_iterations):
            step = RefineStep(iteration=i)

            # GENERATE (or use current_draft from previous refine)
            if current_draft is None and self._gen_fn:
                current_draft = self._gen_fn(context)
            step.draft = current_draft
            self.drafts.append(current_draft)
            context["current_draft"] = current_draft

            # CRITIQUE
            if self._critique_fn:
                step.critique = self._coerce_critique(self._critique_fn(context, current_draft))
            else:
                step.critique = Critique()
            context["last_critique"] = step.critique

            # ACCEPT?
            if self._accept_fn:
                step.accepted = bool(self._accept_fn(context, current_draft, step.critique))
            else:
                step.accepted = step.critique.is_clean

            if step.accepted:
                step.refined = current_draft
                self.steps.append(step)
                break

            # REFINE
            if self._refine_fn:
                current_draft = self._refine_fn(context, current_draft, step.critique)
                step.refined = current_draft
            else:
                # no refiner — cannot improve, stop
                self.steps.append(step)
                break

            self.steps.append(step)

        return self.steps

    @property
    def final_draft(self) -> Any:
        if not self.steps:
            return None
        last = self.steps[-1]
        return last.refined if last.refined is not None else last.draft

    def get_summary(self) -> dict:
        return {
            "iterations": len(self.steps),
            "drafts": len(self.drafts),
            "converged": bool(self.steps and self.steps[-1].accepted),
            "final_issues": len(self.steps[-1].critique.issues) if self.steps and self.steps[-1].critique else 0,
        }
