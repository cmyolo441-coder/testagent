"""ReAct — Reasoning + Acting interleaved strategy"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable
import uuid


@dataclass
class Thought:
    content: str = ""
    reasoning: str = ""
    confidence: float = 0.5


@dataclass
class Action:
    name: str = ""
    parameters: dict = field(default_factory=dict)
    expected_result: str = ""


@dataclass
class Observation:
    content: str = ""
    source: str = ""
    reliability: float = 0.5


@dataclass
class ReActStep:
    id: str = field(default_factory=lambda: f"RA-{uuid.uuid4().hex[:8]}")
    thought: Optional[Thought] = None
    action: Optional[Action] = None
    observation: Optional[Observation] = None
    status: str = "pending"
    iteration: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "thought": {"content": self.thought.content, "confidence": self.thought.confidence} if self.thought else None,
            "action": {"name": self.action.name, "parameters": self.action.parameters} if self.action else None,
            "observation": {"content": self.observation.content, "reliability": self.observation.reliability} if self.observation else None,
            "status": self.status,
            "iteration": self.iteration,
        }


@dataclass
class ReActTrace:
    id: str = field(default_factory=lambda: f"TRACE-{uuid.uuid4().hex[:8]}")
    goal: str = ""
    steps: list[ReActStep] = field(default_factory=list)
    final_answer: Optional[str] = None
    status: str = "running"
    max_iterations: int = 10
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def iteration_count(self) -> int:
        return len(self.steps)

    @property
    def is_done(self) -> bool:
        return self.status in ("completed", "failed") or self.iteration_count >= self.max_iterations

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "steps": [s.to_dict() for s in self.steps],
            "final_answer": self.final_answer,
            "status": self.status,
            "iterations": self.iteration_count,
            "max_iterations": self.max_iterations,
        }


class ReAct:
    """Interleaved reasoning and acting with observation loops."""

    def __init__(self, reasoner: Optional[Callable] = None,
                 actor: Optional[Callable] = None,
                 observer: Optional[Callable] = None):
        self.reasoner = reasoner or self._default_reasoner
        self.actor = actor or self._default_actor
        self.observer = observer or self._default_observer
        self.traces: dict[str, ReActTrace] = {}
        self.knowledge: dict[str, str] = {}

    def run(self, goal: str, max_iterations: int = 10) -> ReActTrace:
        trace = ReActTrace(goal=goal, max_iterations=max_iterations)
        self.traces[trace.id] = trace

        for i in range(max_iterations):
            step = ReActStep(iteration=i + 1)
            # Think
            context = self._build_context(trace)
            thought = self.reasoner(goal, context)
            step.thought = thought
            # Decide if done
            if self._is_answer_sufficient(thought, goal):
                step.status = "completed"
                trace.steps.append(step)
                trace.final_answer = thought.content
                trace.status = "completed"
                return trace
            # Act
            action = self._decide_action(thought, goal, context)
            step.action = action
            step.status = "acting"
            # Observe
            observation = self.observer(action, context)
            step.observation = observation
            step.status = "completed"
            trace.steps.append(step)
            # Update knowledge
            self.knowledge[f"{trace.id}:{i}"] = observation.content

        trace.status = "max_iterations"
        trace.final_answer = self._synthesize_answer(trace)
        return trace

    def continue_running(self, trace_id: str) -> ReActTrace:
        trace = self.traces.get(trace_id)
        if not trace or trace.is_done:
            return trace
        remaining = trace.max_iterations - trace.iteration_count
        for i in range(remaining):
            step = ReActStep(iteration=trace.iteration_count + 1)
            context = self._build_context(trace)
            thought = self.reasoner(trace.goal, context)
            step.thought = thought
            if self._is_answer_sufficient(thought, trace.goal):
                step.status = "completed"
                trace.steps.append(step)
                trace.final_answer = thought.content
                trace.status = "completed"
                return trace
            action = self._decide_action(thought, trace.goal, context)
            step.action = action
            observation = self.observer(action, context)
            step.observation = observation
            step.status = "completed"
            trace.steps.append(step)
        if not trace.is_done:
            trace.status = "max_iterations"
            trace.final_answer = self._synthesize_answer(trace)
        return trace

    def get_trace_summary(self, trace_id: str) -> dict:
        trace = self.traces.get(trace_id)
        if not trace:
            return {"error": "trace not found"}
        thoughts = [s for s in trace.steps if s.thought]
        actions = [s for s in trace.steps if s.action]
        observations = [s for s in trace.steps if s.observation]
        return {
            "id": trace.id,
            "goal": trace.goal,
            "status": trace.status,
            "iterations": trace.iteration_count,
            "thoughts": len(thoughts),
            "actions": len(actions),
            "observations": len(observations),
            "final_answer": trace.final_answer,
        }

    def _build_context(self, trace: ReActTrace) -> dict:
        return {
            "goal": trace.goal,
            "previous_steps": [s.to_dict() for s in trace.steps[-3:]],
            "knowledge": dict(list(self.knowledge.items())[-5:]),
        }

    def _is_answer_sufficient(self, thought: Thought, goal: str) -> bool:
        return thought.confidence > 0.8 and len(thought.content) > 20

    def _decide_action(self, thought: Thought, goal: str, context: dict) -> Action:
        return Action(
            name="search",
            parameters={"query": thought.content[:100]},
            expected_result="Additional information",
        )

    def _synthesize_answer(self, trace: ReActTrace) -> str:
        observations = [s.observation.content for s in trace.steps if s.observation]
        return " | ".join(observations[-3:]) if observations else "Unable to determine answer"

    @staticmethod
    def _default_reasoner(goal: str, context: dict) -> Thought:
        return Thought(
            content=f"Analyzing: {goal}",
            reasoning="Processing available information",
            confidence=0.6,
        )

    @staticmethod
    def _default_actor(action: Action, context: dict) -> str:
        return f"Executed: {action.name}"

    @staticmethod
    def _default_observer(action: Action, context: dict) -> Observation:
        return Observation(
            content=f"Result of {action.name}: completed",
            source="system",
            reliability=0.7,
        )
