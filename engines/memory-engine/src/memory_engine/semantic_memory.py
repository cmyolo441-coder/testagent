"""Semantic Memory — Facts, knowledge, and relationships"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid
import json


@dataclass
class Fact:
    id: str = field(default_factory=lambda: f"FCT-{uuid.uuid4().hex[:12]}")
    subject: str = ""
    predicate: str = ""  # is_a, has_property, relates_to, etc.
    object: str = ""
    confidence: float = 0.8
    source: str = "observed"  # observed, inferred, stated, verified
    context: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    times_observed: int = 1
    last_observed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "confidence": self.confidence,
            "source": self.source,
            "tags": self.tags,
            "times_observed": self.times_observed,
            "created_at": self.created_at,
        }


class SemanticMemory:
    """Manages factual/semantic knowledge."""

    def __init__(self, store=None):
        self.store = store
        self.facts: dict[str, Fact] = {}

    def add_fact(self, subject: str, predicate: str, obj: str,
                 confidence: float = 0.8, source: str = "observed",
                 tags: list[str] = None, context: dict = None) -> Fact:
        # Check if similar fact exists
        existing = self._find_similar(subject, predicate, obj)
        if existing:
            existing.times_observed += 1
            existing.confidence = min(1.0, (existing.confidence + confidence) / 2)
            existing.last_observed = datetime.now(timezone.utc).isoformat()
            return existing

        fact = Fact(
            subject=subject,
            predicate=predicate,
            object=obj,
            confidence=confidence,
            source=source,
            tags=tags or [],
            context=context or {},
        )
        self.facts[fact.id] = fact

        if self.store:
            from memory_engine.stores.sqlite_store import MemoryRecord
            record = MemoryRecord(
                memory_type="semantic",
                content=f"{subject} {predicate} {obj}",
                context={"subject": subject, "predicate": predicate, "object": obj},
                importance=confidence,
                tags=tags or [],
            )
            self.store.store(record)

        return fact

    def query(self, subject: str = None, predicate: str = None,
              obj: str = None, min_confidence: float = 0.0) -> list[Fact]:
        results = []
        for fact in self.facts.values():
            if subject and fact.subject.lower() != subject.lower():
                continue
            if predicate and fact.predicate.lower() != predicate.lower():
                continue
            if obj and fact.object.lower() != obj.lower():
                continue
            if fact.confidence < min_confidence:
                continue
            results.append(fact)
        return results

    def get_facts_about(self, entity: str) -> list[Fact]:
        results = []
        for fact in self.facts.values():
            if entity.lower() in (fact.subject.lower(), fact.object.lower()):
                results.append(fact)
        return results

    def get_relations(self, subject: str) -> list[tuple[str, str]]:
        relations = []
        for fact in self.facts.values():
            if fact.subject.lower() == subject.lower():
                relations.append((fact.predicate, fact.object))
        return relations

    def confidence_check(self, fact_id: str) -> dict:
        fact = self.facts.get(fact_id)
        if not fact:
            return {"error": "Fact not found"}
        return {
            "fact": fact.to_dict(),
            "reliability": "high" if fact.confidence > 0.8 else "medium" if fact.confidence > 0.5 else "low",
            "observation_count": fact.times_observed,
            "source_trust": fact.source,
        }

    def _find_similar(self, subject: str, predicate: str, obj: str) -> Optional[Fact]:
        for fact in self.facts.values():
            if (fact.subject.lower() == subject.lower() and
                fact.predicate.lower() == predicate.lower() and
                fact.object.lower() == obj.lower()):
                return fact
        return None

    def get_stats(self) -> dict:
        facts = list(self.facts.values())
        predicates = {}
        for f in facts:
            predicates[f.predicate] = predicates.get(f.predicate, 0) + 1
        avg_conf = sum(f.confidence for f in facts) / len(facts) if facts else 0
        return {
            "total_facts": len(facts),
            "predicates": predicates,
            "avg_confidence": avg_conf,
        }
