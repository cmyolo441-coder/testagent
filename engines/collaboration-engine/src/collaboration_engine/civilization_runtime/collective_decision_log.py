"""Collective Decision Log — Append-only ledger of group decisions."""
from dataclasses import dataclass, field
from typing import Optional
import time
import uuid


@dataclass
class Decision:
    id: str = field(default_factory=lambda: f"DEC-{uuid.uuid4().hex[:8]}")
    topic: str = ""
    options: list[str] = field(default_factory=list)
    votes_for_each: dict[str, int] = field(default_factory=dict)
    winner: Optional[str] = None
    participant_ids: list[str] = field(default_factory=list)
    ts: float = field(default_factory=time.time)
    rationale: str = ""


class CollectiveDecisionLog:
    """Append-only audit log of collective decisions."""

    def __init__(self):
        self.entries: list[Decision] = []

    def record(self, topic: str, options: list[str], votes_for_each: dict[str, int],
               participant_ids: list[str], winner: Optional[str] = None,
               rationale: str = "") -> Decision:
        if winner is None and votes_for_each:
            winner = max(votes_for_each.items(), key=lambda kv: kv[1])[0]
        decision = Decision(
            topic=topic,
            options=list(options),
            votes_for_each=dict(votes_for_each),
            winner=winner,
            participant_ids=list(participant_ids),
            rationale=rationale,
        )
        self.entries.append(decision)
        return decision

    def list_recent(self, n: int = 10) -> list[Decision]:
        return list(self.entries[-n:][::-1])

    def search(self, topic: str) -> list[Decision]:
        needle = topic.lower()
        return [d for d in self.entries if needle in d.topic.lower()]

    def by_participant(self, agent_id: str) -> list[Decision]:
        return [d for d in self.entries if agent_id in d.participant_ids]

    def get(self, decision_id: str) -> Optional[Decision]:
        for d in self.entries:
            if d.id == decision_id:
                return d
        return None

    def stats(self) -> dict:
        topics: dict[str, int] = {}
        for d in self.entries:
            topics[d.topic] = topics.get(d.topic, 0) + 1
        return {
            "total": len(self.entries),
            "unique_topics": len(topics),
            "top_topics": sorted(topics.items(), key=lambda kv: kv[1], reverse=True)[:5],
        }
