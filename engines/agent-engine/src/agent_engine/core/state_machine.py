"""State Machine — Agent state transitions with guards"""
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional


class AgentState(Enum):
    IDLE = "idle"
    OBSERVING = "observing"
    THINKING = "thinking"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    REFLECTING = "reflecting"
    WAITING_APPROVAL = "waiting_approval"
    WAITING_INPUT = "waiting_input"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Transition:
    from_state: AgentState
    to_state: AgentState
    guard: Callable[[], bool] = None
    action: Callable[[], None] = None
    name: str = ""


class AgentStateMachine:
    """Manage agent state transitions with guards and actions."""

    def __init__(self):
        self.current_state = AgentState.IDLE
        self.transitions: list[Transition] = []
        self.history: list[tuple[AgentState, AgentState, str]] = []
        self._setup_default_transitions()

    def _setup_default_transitions(self):
        self.add_transition(AgentState.IDLE, AgentState.OBSERVING, name="start")
        self.add_transition(AgentState.OBSERVING, AgentState.THINKING, name="observed")
        self.add_transition(AgentState.THINKING, AgentState.PLANNING, name="thought")
        self.add_transition(AgentState.PLANNING, AgentState.EXECUTING, name="planned")
        self.add_transition(AgentState.EXECUTING, AgentState.VERIFYING, name="executed")
        self.add_transition(AgentState.VERIFYING, AgentState.REFLECTING, name="verified")
        self.add_transition(AgentState.REFLECTING, AgentState.OBSERVING, name="reflected", guard=lambda: True)
        self.add_transition(AgentState.REFLECTING, AgentState.COMPLETED, name="done")
        self.add_transition(AgentState.THINKING, AgentState.WAITING_APPROVAL, name="needs_approval")
        self.add_transition(AgentState.WAITING_APPROVAL, AgentState.EXECUTING, name="approved")
        self.add_transition(AgentState.WAITING_APPROVAL, AgentState.CANCELLED, name="rejected")
        self.add_transition(AgentState.EXECUTING, AgentState.RECOVERING, name="error", guard=lambda: True)
        self.add_transition(AgentState.RECOVERING, AgentState.THINKING, name="recovered")
        self.add_transition(AgentState.RECOVERING, AgentState.FAILED, name="unrecoverable")

    def add_transition(self, from_state: AgentState, to_state: AgentState,
                      guard: Callable = None, action: Callable = None, name: str = ""):
        self.transitions.append(Transition(
            from_state=from_state,
            to_state=to_state,
            guard=guard,
            action=action,
            name=name,
        ))

    def can_transition(self, to_state: AgentState) -> bool:
        for t in self.transitions:
            if t.from_state == self.current_state and t.to_state == to_state:
                if t.guard is None or t.guard():
                    return True
        return False

    def transition(self, to_state: AgentState, name: str = "") -> bool:
        for t in self.transitions:
            if t.from_state == self.current_state and t.to_state == to_state:
                if t.guard is None or t.guard():
                    old_state = self.current_state
                    if t.action:
                        t.action()
                    self.current_state = to_state
                    self.history.append((old_state, to_state, name or t.name))
                    return True
        return False

    def get_available_transitions(self) -> list[AgentState]:
        available = []
        for t in self.transitions:
            if t.from_state == self.current_state:
                if t.guard is None or t.guard():
                    available.append(t.to_state)
        return available

    def get_history(self) -> list[dict]:
        return [
            {"from": f.value, "to": t.value, "name": n}
            for f, t, n in self.history
        ]
