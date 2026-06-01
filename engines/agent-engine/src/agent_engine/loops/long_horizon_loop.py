"""LongHorizonLoop — durable multi-checkpoint loop for months-long missions."""
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable, Any
from datetime import datetime, timezone


@dataclass
class Checkpoint:
    step_index: int
    state: dict = field(default_factory=dict)
    note: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class HorizonStep:
    index: int
    action_result: Any = None
    checkpointed: bool = False
    hibernated: bool = False
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class LongHorizonLoop:
    """Durable long-running loop with checkpoints, hibernate/wake, and resume."""

    def __init__(
        self,
        max_steps: int = 1_000_000,
        checkpoint_every: int = 100,
    ):
        self.max_steps = max_steps
        self.checkpoint_every = max(1, checkpoint_every)
        self.steps: list[HorizonStep] = []
        self.checkpoints: list[Checkpoint] = []
        self.state: dict = {
            "step_index": 0,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "hibernated": False,
            "mission_data": {},
        }
        self._step_fn: Optional[Callable] = None
        self._checkpoint_fn: Optional[Callable] = None
        self._stop_fn: Optional[Callable] = None
        self._wake_fn: Optional[Callable] = None
        self._hibernate_fn: Optional[Callable] = None

    def set_step(self, fn: Callable):
        self._step_fn = fn

    def set_checkpoint(self, fn: Callable):
        self._checkpoint_fn = fn

    def set_stop(self, fn: Callable):
        self._stop_fn = fn

    def set_wake(self, fn: Callable):
        self._wake_fn = fn

    def set_hibernate(self, fn: Callable):
        self._hibernate_fn = fn

    # ---- durability ----
    def resume(self, state: dict) -> None:
        """Restore loop from a previously-persisted state dict."""
        if not isinstance(state, dict):
            raise TypeError("state must be a dict")
        self.state = dict(state)
        self.state.setdefault("step_index", 0)
        self.state.setdefault("mission_data", {})
        self.state["hibernated"] = False
        self.state["resumed_at"] = datetime.now(timezone.utc).isoformat()

    def snapshot(self) -> dict:
        """Return a JSON-serializable snapshot of current state."""
        return {
            "state": dict(self.state),
            "checkpoints": [asdict(c) for c in self.checkpoints],
            "step_count": len(self.steps),
        }

    def hibernate(self) -> dict:
        """Pause the loop and return a snapshot. Persist this externally."""
        self.state["hibernated"] = True
        self.state["hibernated_at"] = datetime.now(timezone.utc).isoformat()
        if self._hibernate_fn:
            self._hibernate_fn(self.state)
        snap = self.snapshot()
        return snap

    def wake(self, state: Optional[dict] = None) -> None:
        """Wake from hibernation, optionally re-loading state."""
        if state is not None:
            self.resume(state)
        else:
            self.state["hibernated"] = False
            self.state["woken_at"] = datetime.now(timezone.utc).isoformat()
        if self._wake_fn:
            self._wake_fn(self.state)

    # ---- main loop ----
    def run(self, initial_context: dict = None) -> list[HorizonStep]:
        context = dict(initial_context or {})
        context["state"] = self.state

        start = int(self.state.get("step_index", 0))
        for i in range(start, self.max_steps):
            self.state["step_index"] = i

            if self.state.get("hibernated"):
                step = HorizonStep(index=i, hibernated=True)
                self.steps.append(step)
                break

            if self._stop_fn and self._stop_fn(context, self.state):
                break

            step = HorizonStep(index=i)
            if self._step_fn:
                step.action_result = self._step_fn(context, self.state)
                context["last_result"] = step.action_result

            # checkpoint?
            if ((i + 1) % self.checkpoint_every) == 0:
                cp = Checkpoint(
                    step_index=i,
                    state=dict(self.state),
                    note=f"auto@{i}",
                )
                self.checkpoints.append(cp)
                step.checkpointed = True
                if self._checkpoint_fn:
                    try:
                        self._checkpoint_fn(dict(self.state))
                    except Exception:
                        # checkpoint failures must NOT crash a months-long mission
                        pass

            self.steps.append(step)

        return self.steps

    # ---- helpers ----
    def to_json(self) -> str:
        try:
            return json.dumps(self.snapshot(), default=str)
        except Exception:
            return json.dumps({"step_count": len(self.steps)})

    def get_summary(self) -> dict:
        return {
            "steps": len(self.steps),
            "checkpoints": len(self.checkpoints),
            "current_index": self.state.get("step_index", 0),
            "hibernated": bool(self.state.get("hibernated")),
        }
