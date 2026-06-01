"""SelfHealLoop — wrap an action, diagnose failures, apply heal, retry."""
import time
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from datetime import datetime, timezone


@dataclass
class Diagnosis:
    root_cause: str
    suggested_fix: str = ""
    confidence: float = 0.5
    metadata: dict = field(default_factory=dict)


@dataclass
class HealAttempt:
    attempt: int
    error: str = ""
    diagnosis: Optional[Diagnosis] = None
    heal_applied: Any = None
    succeeded: bool = False
    backoff_ms: int = 0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class SelfHealLoop:
    """Run an action with diagnose+heal+retry on failure."""

    def __init__(
        self,
        max_attempts: int = 4,
        base_backoff_ms: int = 100,
        backoff_factor: float = 2.0,
        max_backoff_ms: int = 30_000,
    ):
        self.max_attempts = max_attempts
        self.base_backoff_ms = base_backoff_ms
        self.backoff_factor = backoff_factor
        self.max_backoff_ms = max_backoff_ms
        self.history: list[HealAttempt] = []
        self.result: Any = None
        self._action_fn: Optional[Callable] = None
        self._diagnose_fn: Optional[Callable] = None
        self._heal_fn: Optional[Callable] = None
        self._is_failure_fn: Optional[Callable] = None
        self._sleep_fn: Callable[[float], None] = time.sleep  # injectable for tests

    def set_action(self, fn: Callable):
        self._action_fn = fn

    def set_diagnose(self, fn: Callable):
        self._diagnose_fn = fn

    def set_heal(self, fn: Callable):
        self._heal_fn = fn

    def set_is_failure(self, fn: Callable):
        """Optional: treat non-exception result as failure. fn(result) -> bool."""
        self._is_failure_fn = fn

    def set_sleep(self, fn: Callable):
        self._sleep_fn = fn

    @staticmethod
    def _coerce_diagnosis(raw) -> Diagnosis:
        if isinstance(raw, Diagnosis):
            return raw
        if isinstance(raw, dict):
            return Diagnosis(
                root_cause=str(raw.get("root_cause", "unknown")),
                suggested_fix=str(raw.get("suggested_fix", "")),
                confidence=float(raw.get("confidence", 0.5)),
                metadata=dict(raw.get("metadata", {}) or {}),
            )
        return Diagnosis(root_cause=str(raw) if raw is not None else "unknown")

    def _compute_backoff(self, attempt: int) -> int:
        ms = int(self.base_backoff_ms * (self.backoff_factor ** max(0, attempt - 1)))
        return min(ms, self.max_backoff_ms)

    def run(self, initial_context: dict = None) -> list[HealAttempt]:
        context = dict(initial_context or {})
        if not self._action_fn:
            return self.history

        for attempt in range(1, self.max_attempts + 1):
            rec = HealAttempt(attempt=attempt)
            err_str = ""
            result = None
            failed = False
            try:
                result = self._action_fn(context)
                if self._is_failure_fn and self._is_failure_fn(result):
                    failed = True
                    err_str = f"is_failure_fn flagged result: {str(result)[:200]}"
            except Exception as e:
                failed = True
                err_str = f"{type(e).__name__}: {e}"

            if not failed:
                rec.succeeded = True
                self.result = result
                self.history.append(rec)
                return self.history

            rec.error = err_str
            context["last_error"] = err_str
            context["last_attempt"] = attempt

            # DIAGNOSE
            if self._diagnose_fn:
                rec.diagnosis = self._coerce_diagnosis(self._diagnose_fn(context, err_str))
                context["last_diagnosis"] = rec.diagnosis

            # HEAL
            if self._heal_fn and rec.diagnosis is not None:
                rec.heal_applied = self._heal_fn(context, rec.diagnosis)
                context["last_heal"] = rec.heal_applied

            self.history.append(rec)

            if attempt >= self.max_attempts:
                break

            # BACKOFF
            rec.backoff_ms = self._compute_backoff(attempt)
            self._sleep_fn(rec.backoff_ms / 1000.0)

        return self.history

    def get_summary(self) -> dict:
        return {
            "attempts": len(self.history),
            "succeeded": bool(self.history and self.history[-1].succeeded),
            "last_error": self.history[-1].error if self.history else "",
            "heals_applied": sum(1 for h in self.history if h.heal_applied is not None),
        }
