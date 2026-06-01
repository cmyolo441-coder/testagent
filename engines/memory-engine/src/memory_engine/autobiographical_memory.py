"""Autobiographical Memory — Personal timeline and life events"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class LifeEvent:
    id: str = field(default_factory=lambda: f"LFE-{uuid.uuid4().hex[:12]}")
    title: str = ""
    description: str = ""
    event_type: str = ""  # milestone, achievement, failure, learning, interaction
    significance: float = 0.5  # 0-1, how important this event is to the agent's identity
    emotional_valence: float = 0.0  # -1 (negative) to 1 (positive)
    agent_id: Optional[str] = None
    related_events: list[str] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type,
            "significance": self.significance,
            "emotional_valence": self.emotional_valence,
            "tags": self.tags,
            "timestamp": self.timestamp,
        }


class AutobiographicalMemory:
    """Manages the agent's personal timeline and identity-shaping events."""

    def __init__(self, store=None):
        self.store = store
        self.events: dict[str, LifeEvent] = {}
        self._timeline: list[str] = []

    def store_event(self, title: str, description: str = "",
                    event_type: str = "general", significance: float = 0.5,
                    emotional_valence: float = 0.0, agent_id: str = None,
                    tags: list[str] = None, context: dict = None,
                    duration_ms: int = 0) -> LifeEvent:
        event = LifeEvent(
            title=title,
            description=description,
            event_type=event_type,
            significance=significance,
            emotional_valence=emotional_valence,
            agent_id=agent_id,
            tags=tags or [],
            context=context or {},
            duration_ms=duration_ms,
        )
        self.events[event.id] = event
        self._timeline.append(event.id)
        self._timeline.sort(key=lambda eid: self.events[eid].timestamp)

        if self.store:
            from memory_engine.stores.sqlite_store import MemoryRecord
            record = MemoryRecord(
                memory_type="autobiographical",
                content=f"{event_type}: {title}",
                context={"significance": significance, "valence": emotional_valence},
                importance=significance,
                agent_id=agent_id,
                tags=tags or [],
                metadata={"life_event_id": event.id},
            )
            self.store.store(record)

        return event

    def recall_timeline(self, limit: int = 50, offset: int = 0) -> list[LifeEvent]:
        event_ids = self._timeline[offset:offset + limit]
        return [self.events[eid] for eid in event_ids if eid in self.events]

    def recall_by_type(self, event_type: str, limit: int = 20) -> list[LifeEvent]:
        events = [e for e in self.events.values() if e.event_type == event_type]
        events.sort(key=lambda e: e.significance, reverse=True)
        return events[:limit]

    def recall_by_significance(self, min_significance: float = 0.7,
                               limit: int = 20) -> list[LifeEvent]:
        events = [e for e in self.events.values() if e.significance >= min_significance]
        events.sort(key=lambda e: e.significance, reverse=True)
        return events[:limit]

    def recall_period(self, start: str, end: str) -> list[LifeEvent]:
        events = [
            e for e in self.events.values()
            if start <= e.timestamp <= end
        ]
        events.sort(key=lambda e: e.timestamp)
        return events

    def get_emotional_arc(self) -> list[dict]:
        timeline = self.recall_timeline(limit=100)
        return [
            {
                "timestamp": e.timestamp,
                "valence": e.emotional_valence,
                "title": e.title,
                "significance": e.significance,
            }
            for e in timeline
        ]

    def get_identity_summary(self) -> dict:
        events = list(self.events.values())
        if not events:
            return {"event_count": 0, "dominant_emotion": "neutral", "avg_significance": 0}

        type_counts: dict[str, int] = {}
        total_valence = 0.0
        for e in events:
            type_counts[e.event_type] = type_counts.get(e.event_type, 0) + 1
            total_valence += e.emotional_valence

        dominant_type = max(type_counts, key=type_counts.get) if type_counts else "unknown"
        avg_valence = total_valence / len(events)
        avg_significance = sum(e.significance for e in events) / len(events)

        return {
            "event_count": len(events),
            "dominant_event_type": dominant_type,
            "event_type_distribution": type_counts,
            "avg_emotional_valence": avg_valence,
            "avg_significance": avg_significance,
            "identity_narrative": self._generate_narrative(events),
        }

    def _generate_narrative(self, events: list[LifeEvent]) -> str:
        if not events:
            return "No significant events recorded yet."
        significant = sorted(events, key=lambda e: e.significance, reverse=True)[:5]
        return f"Key experiences: {', '.join(e.title for e in significant)}"

    def get_stats(self) -> dict:
        events = list(self.events.values())
        return {
            "total_events": len(events),
            "types": {t: sum(1 for e in events if e.event_type == t)
                      for t in set(e.event_type for e in events)},
            "avg_significance": sum(e.significance for e in events) / len(events) if events else 0,
        }
