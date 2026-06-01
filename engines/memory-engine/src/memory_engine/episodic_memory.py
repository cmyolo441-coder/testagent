"""Episodic Memory — Store and recall past experiences"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid
import json


@dataclass
class Episode:
    id: str = field(default_factory=lambda: f"EP-{uuid.uuid4().hex[:12]}")
    title: str = ""
    description: str = ""
    event_type: str = ""  # task_completed, error_occurred, decision_made, etc.
    agent_id: Optional[str] = None
    mission_id: Optional[str] = None
    task_id: Optional[str] = None
    outcome: str = ""  # success, failure, partial
    emotion: str = "neutral"  # for sentiment tracking
    importance: float = 0.5
    confidence: float = 0.5
    context: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    lessons: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type,
            "agent_id": self.agent_id,
            "mission_id": self.mission_id,
            "task_id": self.task_id,
            "outcome": self.outcome,
            "importance": self.importance,
            "tags": self.tags,
            "lessons": self.lessons,
            "created_at": self.created_at,
        }


class EpisodicMemory:
    """Manages episodic (experience-based) memory."""

    def __init__(self, store=None):
        self.store = store
        self.episodes: dict[str, Episode] = {}

    def record_episode(self, title: str, event_type: str, outcome: str,
                       description: str = "", mission_id: str = None,
                       task_id: str = None, agent_id: str = None,
                       importance: float = 0.5, tags: list[str] = None,
                       lessons: list[str] = None, context: dict = None) -> Episode:
        episode = Episode(
            title=title,
            description=description,
            event_type=event_type,
            agent_id=agent_id,
            mission_id=mission_id,
            task_id=task_id,
            outcome=outcome,
            importance=importance,
            tags=tags or [],
            lessons=lessons or [],
            context=context or {},
        )
        self.episodes[episode.id] = episode

        # Also store in persistent store if available
        if self.store:
            from memory_engine.stores.sqlite_store import MemoryRecord
            record = MemoryRecord(
                memory_type="episodic",
                content=f"{title}: {description}",
                context={"event_type": event_type, "outcome": outcome},
                importance=importance,
                mission_id=mission_id,
                task_id=task_id,
                agent_id=agent_id,
                tags=tags or [],
                metadata={"lessons": lessons or []},
            )
            self.store.store(record)

        return episode

    def recall_by_event_type(self, event_type: str, limit: int = 10) -> list[Episode]:
        episodes = [e for e in self.episodes.values() if e.event_type == event_type]
        episodes.sort(key=lambda e: e.importance, reverse=True)
        return episodes[:limit]

    def recall_by_mission(self, mission_id: str, limit: int = 20) -> list[Episode]:
        episodes = [e for e in self.episodes.values() if e.mission_id == mission_id]
        episodes.sort(key=lambda e: e.created_at, reverse=True)
        return episodes[:limit]

    def recall_by_outcome(self, outcome: str, limit: int = 10) -> list[Episode]:
        episodes = [e for e in self.episodes.values() if e.outcome == outcome]
        episodes.sort(key=lambda e: e.importance, reverse=True)
        return episodes[:limit]

    def get_lessons_learned(self, mission_id: str = None) -> list[str]:
        lessons = []
        for episode in self.episodes.values():
            if mission_id and episode.mission_id != mission_id:
                continue
            lessons.extend(episode.lessons)
        return list(set(lessons))

    def get_similar_episodes(self, event_type: str, tags: list[str], limit: int = 5) -> list[Episode]:
        scored = []
        for episode in self.episodes.values():
            score = 0
            if episode.event_type == event_type:
                score += 3
            tag_overlap = len(set(tags) & set(episode.tags))
            score += tag_overlap
            if score > 0:
                scored.append((score, episode))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:limit]]

    def get_stats(self) -> dict:
        episodes = list(self.episodes.values())
        outcomes = {}
        for e in episodes:
            outcomes[e.outcome] = outcomes.get(e.outcome, 0) + 1
        return {
            "total_episodes": len(episodes),
            "outcomes": outcomes,
            "avg_importance": sum(e.importance for e in episodes) / len(episodes) if episodes else 0,
        }
