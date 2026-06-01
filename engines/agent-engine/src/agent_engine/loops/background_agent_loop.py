"""BackgroundAgentLoop — lightweight task-poll loop with cancel support."""
import time
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from datetime import datetime, timezone


@dataclass
class BackgroundRecord:
    iteration: int
    task: Any = None
    result: Any = None
    idle: bool = False
    error: str = ""
    duration_ms: float = 0.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class BackgroundAgentLoop:
    """Polls poll_fn() for tasks, runs process_fn(task), sleeps when idle."""

    def __init__(
        self,
        idle_sleep_ms: int = 500,
        max_iterations: Optional[int] = None,
        max_idle_cycles: Optional[int] = None,
    ):
        self.idle_sleep_ms = max(0, idle_sleep_ms)
        self.max_iterations = max_iterations
        self.max_idle_cycles = max_idle_cycles
        self.records: list[BackgroundRecord] = []
        self._poll_fn: Optional[Callable] = None
        self._process_fn: Optional[Callable] = None
        self._cancel_event: Optional[Callable] = None
        self._on_error_fn: Optional[Callable] = None
        self._on_result_fn: Optional[Callable] = None
        self._sleep_fn: Callable[[float], None] = time.sleep

    def set_poll(self, fn: Callable):
        self._poll_fn = fn

    def set_process(self, fn: Callable):
        self._process_fn = fn

    def set_cancel_event(self, fn: Callable):
        """Callable returning bool; True means cancel."""
        self._cancel_event = fn

    def set_on_error(self, fn: Callable):
        self._on_error_fn = fn

    def set_on_result(self, fn: Callable):
        self._on_result_fn = fn

    def set_sleep(self, fn: Callable):
        self._sleep_fn = fn

    def _cancelled(self) -> bool:
        try:
            return bool(self._cancel_event and self._cancel_event())
        except Exception:
            return False

    def run(self, initial_context: dict = None) -> list[BackgroundRecord]:
        context = dict(initial_context or {})
        idle_cycles = 0
        i = 0
        while True:
            if self.max_iterations is not None and i >= self.max_iterations:
                break
            if self._cancelled():
                break

            rec = BackgroundRecord(iteration=i)
            t0 = time.monotonic()

            task = None
            try:
                if self._poll_fn:
                    task = self._poll_fn()
            except Exception as e:
                rec.error = f"poll:{type(e).__name__}:{e}"
                if self._on_error_fn:
                    try:
                        self._on_error_fn(rec.error, None)
                    except Exception:
                        pass

            if task is None:
                rec.idle = True
                rec.duration_ms = (time.monotonic() - t0) * 1000.0
                self.records.append(rec)
                idle_cycles += 1
                if self.max_idle_cycles is not None and idle_cycles >= self.max_idle_cycles:
                    break
                # interruptible sleep — split into ticks so cancel is responsive
                slept = 0
                tick = min(50, self.idle_sleep_ms) if self.idle_sleep_ms > 0 else 0
                while self.idle_sleep_ms > 0 and slept < self.idle_sleep_ms:
                    if self._cancelled():
                        break
                    step_ms = min(tick, self.idle_sleep_ms - slept)
                    self._sleep_fn(step_ms / 1000.0)
                    slept += step_ms
                i += 1
                continue

            idle_cycles = 0
            rec.task = task
            try:
                if self._process_fn:
                    rec.result = self._process_fn(task)
                if self._on_result_fn and rec.result is not None:
                    try:
                        self._on_result_fn(task, rec.result)
                    except Exception:
                        pass
            except Exception as e:
                rec.error = f"process:{type(e).__name__}:{e}"
                if self._on_error_fn:
                    try:
                        self._on_error_fn(rec.error, task)
                    except Exception:
                        pass

            rec.duration_ms = (time.monotonic() - t0) * 1000.0
            self.records.append(rec)
            i += 1

        return self.records

    def get_summary(self) -> dict:
        processed = [r for r in self.records if not r.idle and not r.error]
        return {
            "iterations": len(self.records),
            "processed": len(processed),
            "idle": sum(1 for r in self.records if r.idle),
            "errors": sum(1 for r in self.records if r.error),
            "cancelled": self._cancelled(),
        }
