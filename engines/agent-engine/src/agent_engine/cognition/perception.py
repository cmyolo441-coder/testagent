"""Perception — Parses raw observations into typed Percepts with salience scoring."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import deque
from typing import Optional
import re
import uuid


PERCEPT_KIND_PATTERNS: dict[str, list[str]] = {
    "error": [r"\berror\b", r"\bexception\b", r"\bfail(ed|ure)?\b", r"\btraceback\b", r"\bpanic\b"],
    "warning": [r"\bwarn(ing)?\b", r"\bdeprecat", r"\bnotice\b"],
    "success": [r"\bsuccess\b", r"\bcompleted\b", r"\bdone\b", r"\bok\b", r"\bpassed\b"],
    "question": [r"\?$", r"\bwhat\b", r"\bwhy\b", r"\bhow\b", r"\bwhen\b", r"\bwhere\b"],
    "command": [r"^\$\s", r"^>\s", r"\brun\b", r"\bexecute\b", r"\bdeploy\b"],
    "metric": [r"\b\d+(\.\d+)?\s*(ms|MB|GB|%|req/s|qps)\b", r"\blatency\b", r"\bthroughput\b"],
    "event": [r"\bevent\b", r"\btriggered\b", r"\boccurred\b"],
}

HIGH_SALIENCE_KEYWORDS = {
    "critical", "urgent", "fatal", "security", "breach", "outage",
    "down", "exception", "error", "fail", "alert", "emergency",
}

ENTITY_PATTERNS: list[tuple[str, str]] = [
    ("url", r"https?://[\w\-./:%?&=#]+"),
    ("ip", r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
    ("path", r"(?:/[\w\-.]+)+/?"),
    ("number", r"\b\d+(?:\.\d+)?\b"),
    ("identifier", r"\b[A-Z][A-Z0-9_]{2,}-[A-Za-z0-9]+\b"),
    ("email", r"[\w.+-]+@[\w-]+\.[\w.-]+"),
]


@dataclass
class Percept:
    id: str = field(default_factory=lambda: f"PERCEPT-{uuid.uuid4().hex[:8]}")
    kind: str = "observation"
    text: str = ""
    entities: list[dict] = field(default_factory=list)
    salience: float = 0.0
    source: str = "unknown"
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Perception:
    """Parses raw observation strings into typed Percepts."""

    def __init__(self, capacity: int = 200):
        self.capacity = capacity
        self.recent: deque[Percept] = deque(maxlen=capacity)

    def _classify_kind(self, text: str) -> str:
        lowered = text.lower()
        best_kind = "observation"
        best_hits = 0
        for kind, patterns in PERCEPT_KIND_PATTERNS.items():
            hits = sum(1 for p in patterns if re.search(p, lowered))
            if hits > best_hits:
                best_hits = hits
                best_kind = kind
        return best_kind

    def _extract_entities(self, text: str) -> list[dict]:
        entities: list[dict] = []
        for ent_type, pattern in ENTITY_PATTERNS:
            for match in re.finditer(pattern, text):
                value = match.group(0)
                entities.append({
                    "type": ent_type,
                    "value": value,
                    "span": [match.start(), match.end()],
                })
        # Deduplicate by (type, value)
        seen: set[tuple[str, str]] = set()
        deduped: list[dict] = []
        for e in entities:
            key = (e["type"], e["value"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(e)
        return deduped

    def salience_of(self, percept: Percept) -> float:
        text = percept.text or ""
        length = len(text)
        # Base from length (saturates around 400 chars).
        length_component = min(1.0, length / 400.0) * 0.4
        # Keyword component.
        lowered = text.lower()
        keyword_hits = sum(1 for kw in HIGH_SALIENCE_KEYWORDS if kw in lowered)
        keyword_component = min(1.0, keyword_hits / 3.0) * 0.4
        # Entity component (more named items = more salient).
        entity_component = min(1.0, len(percept.entities) / 5.0) * 0.15
        # Kind boost.
        kind_boost = {
            "error": 0.15,
            "warning": 0.08,
            "metric": 0.05,
            "question": 0.05,
            "command": 0.05,
            "success": 0.02,
            "event": 0.03,
            "observation": 0.0,
        }.get(percept.kind, 0.0)
        score = length_component + keyword_component + entity_component + kind_boost
        return round(min(1.0, score), 4)

    def observe(self, text: str, source: str = "unknown") -> Percept:
        text = (text or "").strip()
        kind = self._classify_kind(text)
        entities = self._extract_entities(text)
        percept = Percept(kind=kind, text=text, entities=entities, source=source)
        percept.salience = self.salience_of(percept)
        self.recent.append(percept)
        return percept

    def summarize(self, k: int = 10) -> dict:
        k = max(1, int(k))
        items = list(self.recent)
        top = sorted(items, key=lambda p: p.salience, reverse=True)[:k]
        kind_counts: dict[str, int] = {}
        source_counts: dict[str, int] = {}
        entity_total = 0
        salience_sum = 0.0
        for p in items:
            kind_counts[p.kind] = kind_counts.get(p.kind, 0) + 1
            source_counts[p.source] = source_counts.get(p.source, 0) + 1
            entity_total += len(p.entities)
            salience_sum += p.salience
        avg_sal = (salience_sum / len(items)) if items else 0.0
        return {
            "total_percepts": len(items),
            "capacity": self.capacity,
            "kind_counts": kind_counts,
            "source_counts": source_counts,
            "entity_total": entity_total,
            "average_salience": round(avg_sal, 4),
            "top": [
                {
                    "id": p.id,
                    "kind": p.kind,
                    "salience": p.salience,
                    "text": p.text[:140],
                    "source": p.source,
                }
                for p in top
            ],
        }

    def clear(self) -> None:
        self.recent.clear()

    def last(self, n: int = 1) -> list[Percept]:
        if n <= 0:
            return []
        return list(self.recent)[-n:]
