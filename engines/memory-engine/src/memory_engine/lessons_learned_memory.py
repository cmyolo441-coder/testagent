"""Lessons Learned Memory — Capture and retrieve learned lessons"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class Lesson:
    id: str = field(default_factory=lambda: f"LSS-{uuid.uuid4().hex[:12]}")
    title: str = ""
    description: str = ""
    topic: str = ""  # coding, architecture, communication, debugging, deployment
    category: str = ""  # best_practice, anti_pattern, insight, rule_of_thumb
    source: str = ""  # failure_analysis, success_pattern, observation, external
    confidence: float = 0.7
    applicability: str = "general"  # general, project_specific, mission_specific
    related_lessons: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    counter_examples: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    mission_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    times_applied: int = 0
    times_helpful: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def effectiveness(self) -> float:
        if self.times_applied == 0:
            return 0.0
        return self.times_helpful / self.times_applied

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "topic": self.topic,
            "category": self.category,
            "source": self.source,
            "confidence": self.confidence,
            "effectiveness": self.effectiveness,
            "times_applied": self.times_applied,
            "tags": self.tags,
            "created_at": self.created_at,
        }


class LessonsLearned:
    """Captures, organizes, and retrieves learned lessons."""

    def __init__(self, store=None):
        self.store = store
        self.lessons: dict[str, Lesson] = {}
        self._topic_index: dict[str, list[str]] = {}
        self._category_index: dict[str, list[str]] = {}

    def store_lesson(self, title: str, description: str = "",
                     topic: str = "general", category: str = "insight",
                     source: str = "observation", confidence: float = 0.7,
                     applicability: str = "general", examples: list[str] = None,
                     counter_examples: list[str] = None, evidence: list[str] = None,
                     mission_id: str = None, task_id: str = None,
                     agent_id: str = None, tags: list[str] = None) -> Lesson:
        lesson = Lesson(
            title=title,
            description=description,
            topic=topic,
            category=category,
            source=source,
            confidence=confidence,
            applicability=applicability,
            examples=examples or [],
            counter_examples=counter_examples or [],
            evidence=evidence or [],
            mission_id=mission_id,
            task_id=task_id,
            agent_id=agent_id,
            tags=tags or [],
        )
        self.lessons[lesson.id] = lesson

        if topic not in self._topic_index:
            self._topic_index[topic] = []
        self._topic_index[topic].append(lesson.id)

        if category not in self._category_index:
            self._category_index[category] = []
        self._category_index[category].append(lesson.id)

        if self.store:
            from memory_engine.stores.sqlite_store import MemoryRecord
            record = MemoryRecord(
                memory_type="lesson",
                content=f"Lesson: {title} ({topic}/{category})",
                context={"topic": topic, "category": category, "source": source},
                importance=confidence,
                tags=tags or [],
                mission_id=mission_id,
                task_id=task_id,
                agent_id=agent_id,
                metadata={"lesson_id": lesson.id},
            )
            self.store.store(record)

        return lesson

    def get_lessons(self, topic: str = None, category: str = None,
                    min_confidence: float = 0.0, limit: int = 50) -> list[Lesson]:
        results = list(self.lessons.values())
        if topic:
            results = [l for l in results if l.topic == topic]
        if category:
            results = [l for l in results if l.category == category]
        if min_confidence > 0:
            results = [l for l in results if l.confidence >= min_confidence]
        results.sort(key=lambda l: l.confidence, reverse=True)
        return results[:limit]

    def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        return self.lessons.get(lesson_id)

    def search(self, query: str) -> list[Lesson]:
        q = query.lower()
        return [
            l for l in self.lessons.values()
            if q in l.title.lower() or q in l.description.lower() or q in l.topic.lower()
        ]

    def apply_lesson(self, lesson_id: str, was_helpful: bool = True) -> bool:
        lesson = self.lessons.get(lesson_id)
        if not lesson:
            return False
        lesson.times_applied += 1
        if was_helpful:
            lesson.times_helpful += 1
        lesson.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def get_most_effective(self, min_applications: int = 3, limit: int = 10) -> list[Lesson]:
        effective = [
            l for l in self.lessons.values()
            if l.times_applied >= min_applications
        ]
        effective.sort(key=lambda l: l.effectiveness, reverse=True)
        return effective[:limit]

    def get_untested(self) -> list[Lesson]:
        return [l for l in self.lessons.values() if l.times_applied == 0]

    def link_lessons(self, lesson_id_a: str, lesson_id_b: str) -> bool:
        a = self.lessons.get(lesson_id_a)
        b = self.lessons.get(lesson_id_b)
        if not a or not b:
            return False
        if lesson_id_b not in a.related_lessons:
            a.related_lessons.append(lesson_id_b)
        if lesson_id_a not in b.related_lessons:
            b.related_lessons.append(lesson_id_a)
        return True

    def get_topic_summary(self) -> dict[str, dict]:
        summary = {}
        for topic, ids in self._topic_index.items():
            lessons = [self.lessons[lid] for lid in ids if lid in self.lessons]
            if lessons:
                summary[topic] = {
                    "count": len(lessons),
                    "avg_confidence": sum(l.confidence for l in lessons) / len(lessons),
                    "avg_effectiveness": (
                        sum(l.effectiveness for l in lessons) / len(lessons)
                        if any(l.times_applied > 0 for l in lessons)
                        else 0.0
                    ),
                }
        return summary

    def get_stats(self) -> dict:
        lessons = list(self.lessons.values())
        return {
            "total_lessons": len(lessons),
            "topics": {t: len(ids) for t, ids in self._topic_index.items()},
            "categories": {c: len(ids) for c, ids in self._category_index.items()},
            "total_applications": sum(l.times_applied for l in lessons),
            "avg_confidence": (
                sum(l.confidence for l in lessons) / len(lessons) if lessons else 0
            ),
        }
