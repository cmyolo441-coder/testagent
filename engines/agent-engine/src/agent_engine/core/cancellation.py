"""Cancellation — Thread-safe cancellation token with parent/child linking."""
from dataclasses import dataclass, field
from typing import Optional, Callable
from datetime import datetime, timezone
import threading
import uuid


class CancelledError(Exception):
    """Raised when an operation is cancelled."""

    def __init__(self, reason: Optional[str] = None, token_id: Optional[str] = None):
        self.reason = reason
        self.token_id = token_id
        super().__init__(reason or "Operation cancelled")


@dataclass
class CancellationInfo:
    cancelled: bool = False
    reason: Optional[str] = None
    ts: Optional[str] = None


class CancellationToken:
    """Thread-safe cancellation flag with nested (parent->child) linking."""

    def __init__(self, token_id: Optional[str] = None):
        self.id: str = token_id or f"CTK-{uuid.uuid4().hex[:8]}"
        self._lock = threading.RLock()
        self._cancelled: bool = False
        self._reason: Optional[str] = None
        self._cancelled_at: Optional[str] = None
        self._children: list["CancellationToken"] = []
        self._callbacks: list[Callable[["CancellationToken"], None]] = []

    @property
    def is_cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    @property
    def reason(self) -> Optional[str]:
        with self._lock:
            return self._reason

    def cancel(self, reason: Optional[str] = None) -> bool:
        """Cancel this token and propagate to all linked children."""
        callbacks_to_run: list[Callable[["CancellationToken"], None]] = []
        children_to_cancel: list["CancellationToken"] = []
        with self._lock:
            if self._cancelled:
                return False
            self._cancelled = True
            self._reason = reason
            self._cancelled_at = datetime.now(timezone.utc).isoformat()
            callbacks_to_run = list(self._callbacks)
            children_to_cancel = list(self._children)

        for child in children_to_cancel:
            child.cancel(reason)
        for cb in callbacks_to_run:
            try:
                cb(self)
            except Exception:
                pass
        return True

    def raise_if_cancelled(self) -> None:
        if self.is_cancelled:
            raise CancelledError(reason=self._reason, token_id=self.id)

    def link(self, child: "CancellationToken") -> "CancellationToken":
        """Link a child token: cancelling the parent cancels the child."""
        already_cancelled = False
        reason = None
        with self._lock:
            if child is self or child in self._children:
                return child
            self._children.append(child)
            if self._cancelled:
                already_cancelled = True
                reason = self._reason
        if already_cancelled:
            child.cancel(reason)
        return child

    def child(self) -> "CancellationToken":
        """Create a new child token linked to this token."""
        c = CancellationToken()
        self.link(c)
        return c

    def on_cancel(self, callback: Callable[["CancellationToken"], None]) -> None:
        """Register a callback fired when this token is cancelled."""
        run_now = False
        with self._lock:
            if self._cancelled:
                run_now = True
            else:
                self._callbacks.append(callback)
        if run_now:
            try:
                callback(self)
            except Exception:
                pass

    def info(self) -> CancellationInfo:
        with self._lock:
            return CancellationInfo(
                cancelled=self._cancelled,
                reason=self._reason,
                ts=self._cancelled_at,
            )

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "id": self.id,
                "cancelled": self._cancelled,
                "reason": self._reason,
                "cancelled_at": self._cancelled_at,
                "children": len(self._children),
                "callbacks": len(self._callbacks),
            }
