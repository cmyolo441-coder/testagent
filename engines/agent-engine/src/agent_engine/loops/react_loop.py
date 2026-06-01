"""ReActLoop — Reason → Act → Observe cycle (Yao et al. ReAct pattern)."""
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from datetime import datetime, timezone


@dataclass
class ReActStep:
    iteration: int
    reasoning: str = ""
    action: dict = field(default_factory=dict)
    action_result: Any = None
    observation: str = ""
    should_continue: bool = True
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class ReActLoop:
    """Reason → Act → Observe cycle. Loops until stop_fn or max_iter."""

    def __init__(self, max_iterations: int = 25):
        self.max_iterations = max_iterations
        self.steps: list[ReActStep] = []
        self._think_fn: Optional[Callable] = None
        self._act_fn: Optional[Callable] = None
        self._observe_fn: Optional[Callable] = None
        self._stop_fn: Optional[Callable] = None
        self._tool_invoke_fn: Optional[Callable] = None

    def set_think(self, fn: Callable):
        self._think_fn = fn

    def set_act(self, fn: Callable):
        self._act_fn = fn

    def set_observe(self, fn: Callable):
        self._observe_fn = fn

    def set_stop(self, fn: Callable):
        self._stop_fn = fn

    def set_tool_invoke(self, fn: Callable):
        """Optional: how to actually execute {tool, args} from act_fn."""
        self._tool_invoke_fn = fn

    def run(self, initial_context: dict = None) -> list[ReActStep]:
        context = dict(initial_context or {})
        context.setdefault("history", [])

        for i in range(self.max_iterations):
            step = ReActStep(iteration=i)

            # REASON
            if self._think_fn:
                step.reasoning = self._think_fn(context) or ""
                context["last_reasoning"] = step.reasoning

            # Check stop BEFORE acting (lets reasoner signal done)
            if self._stop_fn and self._stop_fn(context):
                step.should_continue = False
                self.steps.append(step)
                break

            # ACT — produce {tool, args}
            if self._act_fn:
                action = self._act_fn(context, step.reasoning) or {}
                if not isinstance(action, dict):
                    action = {"tool": "noop", "args": {"raw": action}}
                step.action = action
                # Execute tool if invoker available
                if self._tool_invoke_fn and action.get("tool"):
                    step.action_result = self._tool_invoke_fn(
                        action.get("tool"), action.get("args", {})
                    )
                context["last_action"] = step.action
                context["last_action_result"] = step.action_result

            # OBSERVE
            if self._observe_fn:
                step.observation = self._observe_fn(context, step.action_result) or ""
                context["last_observation"] = step.observation

            context["history"].append({
                "i": i,
                "reasoning": step.reasoning,
                "action": step.action,
                "observation": step.observation,
            })
            self.steps.append(step)

            if self._stop_fn and self._stop_fn(context):
                step.should_continue = False
                break

        return self.steps

    def get_summary(self) -> dict:
        return {
            "iterations": len(self.steps),
            "stopped_early": bool(self.steps and not self.steps[-1].should_continue),
            "last_observation": self.steps[-1].observation[:200] if self.steps else "",
        }
