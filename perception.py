"""Perception — parse raw observation strings into typed Percepts"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime, timezone
from collections import deque
import re
import uuid


class Sentiment(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class Urgency(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PerceptSource(Enum):
    USER = "user"
    SYSTEM = "system"
    TOOL = "tool"
    SENSOR = "sensor"
    AGENT = "agent"
    UNKNOWN = "unknown"


@dataclass
class Percept:
    percept_id: str
    raw: str
    entities: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    sentiment: Sentiment = Sentiment.NEUTRAL
    urgency: Urgency = Urgency.LOW
    source: PerceptSource = PerceptSource.UNKNOWN
    salience: float = 0.0
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class Perception:
    """Parse raw observation strings into typed Percepts and track recency."""

    POSITIVE_WORDS = {
        "good", "great", "excellent", "love", "happy", "success", "wonderful",
        "awesome", "perfect", "amazing", "passed", "ok", "okay", "done",
    }
    NEGATIVE_WORDS = {
        "bad", "terrible", "hate", "angry", "fail", "failed", "broken",
        "error", "crash", "bug", "wrong", "issue", "problem", "blocked",
    }
    URGENCY_CRITICAL = {"asap", "now", "emergency", "critical", "urgent", "p0", "sev0", "sev1"}
    URGENCY_HIGH = {"soon", "today", "high priority", "p1", "important"}
    URGENCY_MEDIUM = {"this week", "p2", "moderate"}
    ENTITY_REGEX = re.compile(r"\b([A-Z][a-zA-Z0-9_\-]{2,})\b")
    HASHTAG_REGEX = re.compile(r"#([A-Za-z0-9_\-]+)")
    MENTION_REGEX = re.compile(r"@([A-Za-z0-9_\-]+)")

    def __init__(self, max_history: int = 200):
        self.history: deque[Percept] = deque(maxlen=max_history)

    def perceive(self, raw: str, source: PerceptSource = PerceptSource.UNKNOWN) -> Percept:
        text = raw.strip()
        lowered = text.lower()
        entities = self._extract_entities(text)
        tags = self._extract_tags(text)
        sentiment = self._score_sentiment(lowered)
        urgency = self._score_urgency(lowered)
        percept = Percept(
            percept_id=f"PERCEPT-{uuid.uuid4().hex[:8]}",
            raw=text,
            entities=entities,
            tags=tags,
            sentiment=sentiment,
            urgency=urgency,
            source=source,
        )
        percept.salience = self.salience(percept)
        self.history.append(percept)
        return percept

    def _extract_entities(self, text: str) -> list[str]:
        found = []
        seen = set()
        for match in self.ENTITY_REGEX.findall(text):
            if match.lower() in seen:
                continue
            seen.add(match.lower())
            found.append(match)
        for m in self.MENTION_REGEX.findall(text):
            key = "@" + m
            if key.lower() not in seen:
                seen.add(key.lower())
                found.append(key)
        return found

    def _extract_tags(self, text: str) -> list[str]:
        tags = list({t.lower() for t in self.HASHTAG_REGEX.findall(text)})
        tags.sort()
        return tags

    def _score_sentiment(self, lowered: str) -> Sentiment:
        words = set(re.findall(r"[a-zA-Z']+", lowered))
        pos = len(words & self.POSITIVE_WORDS)
        neg = len(words & self.NEGATIVE_WORDS)
        if pos and neg:
            return Sentiment.MIXED
        if pos > neg:
            return Sentiment.POSITIVE
        if neg > pos:
            return Sentiment.NEGATIVE
        return Sentiment.NEUTRAL

    def _score_urgency(self, lowered: str) -> Urgency:
        if any(kw in lowered for kw in self.URGENCY_CRITICAL):
            return Urgency.CRITICAL
        if any(kw in lowered for kw in self.URGENCY_HIGH):
            return Urgency.HIGH
        if any(kw in lowered for kw in self.URGENCY_MEDIUM):
            return Urgency.MEDIUM
        if "!" in lowered:
            return Urgency.HIGH
        return Urgency.LOW

    def salience(self, percept: Percept) -> float:
        score = 0.0
        urgency_weights = {
            Urgency.CRITICAL: 1.0,
            Urgency.HIGH: 0.75,
            Urgency.MEDIUM: 0.5,
            Urgency.LOW: 0.2,
        }
        score += urgency_weights[percept.urgency] * 0.5
        if percept.sentiment in (Sentiment.NEGATIVE, Sentiment.MIXED):
            score += 0.2
        score += min(0.2, 0.04 * len(percept.entities))
        score += min(0.1, 0.02 * len(percept.tags))
        if percept.source == PerceptSource.USER:
            score += 0.1
        return round(min(1.0, score), 4)

    def recent(self, n: int = 10) -> list[Percept]:
        if n <= 0:
            return []
        return list(self.history)[-n:]

    def summarize(self, n: int = 20) -> dict:
        items = self.recent(n)
        if not items:
            return {
                "count": 0,
                "top_entities": [],
                "top_tags": [],
                "sentiment_distribution": {},
                "urgency_distribution": {},
                "mean_salience": 0.0,
            }
        from collections import Counter
        ent_counter: Counter = Counter()
        tag_counter: Counter = Counter()
        sent_counter: Counter = Counter()
        urg_counter: Counter = Counter()
        for p in items:
            ent_counter.update(p.entities)
            tag_counter.update(p.tags)
            sent_counter[p.sentiment.value] += 1
            urg_counter[p.urgency.value] += 1
        mean_sal = sum(p.salience for p in items) / len(items)
        return {
            "count": len(items),
            "top_entities": [e for e, _ in ent_counter.most_common(5)],
            "top_tags": [t for t, _ in tag_counter.most_common(5)],
            "sentiment_distribution": dict(sent_counter),
            "urgency_distribution": dict(urg_counter),
            "mean_salience": round(mean_sal, 4),
        }

    def clear(self) -> None:
        self.history.clear()
