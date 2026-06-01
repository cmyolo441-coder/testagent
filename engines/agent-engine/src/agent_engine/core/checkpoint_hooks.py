"""Checkpoint Hooks — Register and execute pre/post checkpoint and restore callbacks."""
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


class CheckpointPhase(Enum):
    PRE_CHECKPOINT = "pre_checkpoint"
    POST_CHECKPOINT = "post_checkpoint"
    PRE_RESTORE = "pre_restore"
    POST_RESTORE = "post_restore"


@dataclass
class CheckpointEvent:
    id: str = field(default_factory=lambda: f"CKE-{uuid.uuid4().hex[:8]}")
    phase: str = CheckpointPhase.PRE_CHECKPOINT.value
    checkpoint_id: Optional[str] = None
    payload: dict = field(default_factory=dict)
    error: Optional[str] = None
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


HookFn = Callable[[CheckpointEvent], Any]


class CheckpointHooks:
    """Registry of callbacks for checkpoint lifecycle phases."""

    def __init__(self):
        self._hooks: dict[str, list[HookFn]] = {
            CheckpointPhase.PRE_CHECKPOINT.value: [],
            CheckpointPhase.POST_CHECKPOINT.value: [],
            CheckpointPhase.PRE_RESTORE.value: [],
            CheckpointPhase.POST_RESTORE.value: [],
        }
        self.history: list[CheckpointEvent] = []

    def pre_checkpoint(self, fn: HookFn) -> HookFn:
        self._hooks[CheckpointPhase.PRE_CHECKPOINT.value].append(fn)
        return fn

    def post_checkpoint(self, fn: HookFn) -> HookFn:
        self._hooks[CheckpointPhase.POST_CHECKPOINT.value].append(fn)
        return fn

    def pre_restore(self, fn: HookFn) -> HookFn:
        self._hooks[CheckpointPhase.PRE_RESTORE.value].append(fn)
        return fn

    def post_restore(self, fn: HookFn) -> HookFn:
        self._hooks[CheckpointPhase.POST_RESTORE.value].append(fn)
        return fn

    def _execute(
        self,
        phase: CheckpointPhase,
        checkpoint_id: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> CheckpointEvent:
        event = CheckpointEvent(
            phase=phase.value,
            checkpoint_id=checkpoint_id,
            payload=dict(payload or {}),
        )
        errors: list[str] = []
        for hook in self._hooks.get(phase.value, []):
            try:
                hook(event)
            except Exception as e:
                errors.append(f"{getattr(hook, '__name__', 'hook')}: {e}")
        if errors:
            event.error = "; ".join(errors)
        self.history.append(event)
        return event

    def execute_pre_checkpoint(
        self, checkpoint_id: Optional[str] = None, payload: Optional[dict] = None
    ) -> CheckpointEvent:
        return self._execute(CheckpointPhase.PRE_CHECKPOINT, checkpoint_id, payload)

    def execute_post_checkpoint(
        self, checkpoint_id: Optional[str] = None, payload: Optional[dict] = None
    ) -> CheckpointEvent:
        return self._execute(CheckpointPhase.POST_CHECKPOINT, checkpoint_id, payload)

    def execute_pre_restore(
        self, checkpoint_id: Optional[str] = None, payload: Optional[dict] = None
    ) -> CheckpointEvent:
        return self._execute(CheckpointPhase.PRE_RESTORE, checkpoint_id, payload)

    def execute_post_restore(
        self, checkpoint_id: Optional[str] = None, payload: Optional[dict] = None
    ) -> CheckpointEvent:
        return self._execute(CheckpointPhase.POST_RESTORE, checkpoint_id, payload)

    def clear(self) -> None:
        for k in self._hooks:
            self._hooks[k] = []

    def to_dict(self) -> dict:
        return {
            "registered": {k: len(v) for k, v in self._hooks.items()},
            "history": len(self.history),
        }
