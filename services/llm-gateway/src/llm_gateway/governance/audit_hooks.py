"""Audit Hooks — Pluggable request/response/error observers for the gateway."""
from __future__ import annotations

import hashlib
import json
import logging
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Callable, Optional

_log = logging.getLogger(__name__)

VALID_KINDS = {"on_request", "on_response", "on_error"}


@dataclass
class HookEvent:
    ts: str
    kind: str  # 'request' | 'response' | 'error'
    model: Optional[str] = None
    user_id: Optional[str] = None
    tokens: Optional[int] = None
    cost: Optional[float] = None
    payload_hash: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class AuditHooks:
    """Register handlers for request/response/error events and dispatch them.

    Handlers that raise are caught and logged so a misbehaving observer cannot
    break the gateway hot path. The ``history`` deque is capped at 10,000 events.
    """

    HISTORY_CAP = 10_000

    def __init__(self):
        self._handlers: dict[str, list[Callable[[HookEvent], None]]] = {
            k: [] for k in VALID_KINDS
        }
        self.history: deque[HookEvent] = deque(maxlen=self.HISTORY_CAP)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register(self, kind: str, fn: Callable[[HookEvent], None]) -> None:
        if kind not in VALID_KINDS:
            raise ValueError(f"Unknown hook kind '{kind}'. Valid: {sorted(VALID_KINDS)}")
        if not callable(fn):
            raise TypeError("Hook handler must be callable")
        self._handlers[kind].append(fn)

    def unregister(self, kind: str, fn: Callable[[HookEvent], None]) -> bool:
        if kind not in VALID_KINDS:
            return False
        try:
            self._handlers[kind].remove(fn)
            return True
        except ValueError:
            return False

    # ------------------------------------------------------------------
    # Emit
    # ------------------------------------------------------------------
    def emit(self, kind: str, **fields: Any) -> HookEvent:
        if kind not in VALID_KINDS:
            raise ValueError(f"Unknown hook kind '{kind}'. Valid: {sorted(VALID_KINDS)}")

        payload = fields.pop("payload", None)
        payload_hash = fields.pop("payload_hash", None)
        if payload_hash is None and payload is not None:
            payload_hash = self._hash_payload(payload)

        metadata = fields.pop("metadata", {}) or {}

        event = HookEvent(
            ts=datetime.now(timezone.utc).isoformat(),
            kind=self._normalize_kind(kind),
            model=fields.pop("model", None),
            user_id=fields.pop("user_id", None),
            tokens=fields.pop("tokens", None),
            cost=fields.pop("cost", None),
            payload_hash=payload_hash,
            metadata={**metadata, **fields},
        )
        self.history.append(event)

        for handler in list(self._handlers.get(kind, [])):
            try:
                handler(event)
            except Exception as exc:  # pragma: no cover — defensive
                _log.warning("audit hook %r raised %s", handler, exc)
                self.history.append(
                    HookEvent(
                        ts=datetime.now(timezone.utc).isoformat(),
                        kind="error",
                        metadata={
                            "hook_error": str(exc),
                            "hook_kind": kind,
                            "handler": getattr(handler, "__name__", repr(handler)),
                        },
                    )
                )
        return event

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------
    def recent(self, n: int = 50) -> list[dict]:
        items = list(self.history)[-n:]
        return [asdict(e) for e in items]

    def clear(self) -> None:
        self.history.clear()

    def __len__(self) -> int:
        return len(self.history)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _hash_payload(payload: Any) -> str:
        try:
            if isinstance(payload, (bytes, bytearray)):
                data = bytes(payload)
            elif isinstance(payload, str):
                data = payload.encode("utf-8")
            else:
                data = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        except (TypeError, ValueError):
            data = repr(payload).encode("utf-8", errors="replace")
        return hashlib.sha256(data).hexdigest()[:16]

    @staticmethod
    def _normalize_kind(kind: str) -> str:
        if kind.startswith("on_"):
            return kind[3:]
        return kind
