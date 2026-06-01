"""Agent Loop — Observe-Think-Act cycle with verification"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Any
from datetime import datetime, timezone


class LoopPhase(Enum):
    OBSERVE = "observe"
    THINK = "think"
    PLAN = "plan"
    ACT = "act"
    VERIFY = "verify"
    REFLECT = "reflect"
    STOP = "stop"


@dataclass
class LoopStep:
    phase: LoopPhase
    iteration: int
    observation: str = ""
    thought: str = ""
    action: dict = None
    action_result: Any = None
    verification: str = ""
    reflection: str = ""
    should_continue: bool = True
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.action is None:
            self.action = {}


class AgentLoop:
    """Core agent execution loop — Observe → Think → Act → Verify → Reflect."""

    def __init__(self, max_iterations: int = 50, verification_enabled: bool = True):
        self.max_iterations = max_iterations
        self.verification_enabled = verification_enabled
        self.steps: list[LoopStep] = []
        self.current_phase = LoopPhase.OBSERVE
        self._observe_fn: Optional[Callable] = None
        self._think_fn: Optional[Callable] = None
        self._act_fn: Optional[Callable] = None
        self._verify_fn: Optional[Callable] = None
        self._reflect_fn: Optional[Callable] = None
        self._stop_fn: Optional[Callable] = None

    def set_observe(self, fn: Callable):
        self._observe_fn = fn

    def set_think(self, fn: Callable):
        self._think_fn = fn

    def set_act(self, fn: Callable):
        self._act_fn = fn

    def set_verify(self, fn: Callable):
        self._verify_fn = fn

    def set_reflect(self, fn: Callable):
        self._reflect_fn = fn

    def set_stop(self, fn: Callable):
        self._stop_fn = fn

    def run(self, initial_context: dict = None) -> list[LoopStep]:
        context = initial_context or {}

        for iteration in range(self.max_iterations):
            step = LoopStep(phase=LoopPhase.OBSERVE, iteration=iteration)

            # OBSERVE
            if self._observe_fn:
                step.observation = self._observe_fn(context)
                context["last_observation"] = step.observation

            # THINK
            self.current_phase = LoopPhase.THINK
            step.phase = LoopPhase.THINK
            if self._think_fn:
                step.thought = self._think_fn(context, step.observation)
                context["last_thought"] = step.thought

            # PLAN (part of think)
            self.current_phase = LoopPhase.PLAN

            # CHECK STOP
            if self._stop_fn and self._stop_fn(context, step):
                step.should_continue = False
                step.phase = LoopPhase.STOP
                self.steps.append(step)
                break

            # ACT
            self.current_phase = LoopPhase.ACT
            step.phase = LoopPhase.ACT
            if self._act_fn:
                step.action_result = self._act_fn(context, step.thought)
                context["last_action_result"] = step.action_result

            # VERIFY
            if self.verification_enabled:
                self.current_phase = LoopPhase.VERIFY
                step.phase = LoopPhase.VERIFY
                if self._verify_fn:
                    step.verification = self._verify_fn(context, step.action_result)
                    context["last_verification"] = step.verification

            # REFLECT
            self.current_phase = LoopPhase.REFLECT
            step.phase = LoopPhase.REFLECT
            if self._reflect_fn:
                step.reflection = self._reflect_fn(context, step)
                context["last_reflection"] = step.reflection

            self.steps.append(step)

        return self.steps

    def get_summary(self) -> dict:
        if not self.steps:
            return {"iterations": 0, "status": "not_started"}
        return {
            "iterations": len(self.steps),
            "final_phase": self.steps[-1].phase.value,
            "last_observation": self.steps[-1].observation[:200] if self.steps else "",
            "last_thought": self.steps[-1].thought[:200] if self.steps else "",
            "verifications": len([s for s in self.steps if s.verification]),
        }
