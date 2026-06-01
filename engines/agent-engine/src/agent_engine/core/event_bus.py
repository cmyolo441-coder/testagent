"""Event Bus — Async event system for agent communication"""
from dataclasses import dataclass, field
from typing import Callable, Any
from datetime import datetime, timezone
from collections import defaultdict
import uuid
import asyncio


@dataclass
class Event:
    id: str = field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:8]}")
    event_type: str = ""
    source: str = ""
    target: str = ""
    data: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    priority: int = 0  # higher = more important
    processed: bool = False


class EventBus:
    """In-process event bus for agent communication."""

    def __init__(self):
        self.subscribers: dict[str, list[Callable]] = defaultdict(list)
        self.wildcard_subscribers: list[Callable] = []
        self.event_history: list[Event] = []
        self.max_history = 1000

    def subscribe(self, event_type: str, handler: Callable):
        self.subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Callable):
        self.wildcard_subscribers.append(handler)

    def unsubscribe(self, event_type: str, handler: Callable):
        if handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)

    def publish(self, event: Event):
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]

        for handler in self.subscribers.get(event.event_type, []):
            try:
                handler(event)
            except Exception as e:
                self._handle_error(event, e)

        for handler in self.wildcard_subscribers:
            try:
                handler(event)
            except Exception as e:
                self._handle_error(event, e)

        event.processed = True

    def emit(self, event_type: str, data: dict = None, source: str = "", target: str = ""):
        event = Event(
            event_type=event_type,
            source=source,
            target=target,
            data=data or {},
        )
        self.publish(event)

    def get_history(self, event_type: str = None, limit: int = 50) -> list[Event]:
        events = self.event_history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def get_stats(self) -> dict:
        types = {}
        for e in self.event_history:
            types[e.event_type] = types.get(e.event_type, 0) + 1
        return {
            "total_events": len(self.event_history),
            "event_types": types,
            "subscribers": {k: len(v) for k, v in self.subscribers.items()},
        }

    def _handle_error(self, event: Event, error: Exception):
        self.emit("event_error", {
            "original_event": event.event_type,
            "error": str(error),
        })
