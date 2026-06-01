"""User Relationship Memory — Track interactions and rapport with users"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class UserInteraction:
    id: str = field(default_factory=lambda: f"USR-{uuid.uuid4().hex[:12]}")
    user_id: str = ""
    user_name: str = ""
    interaction_type: str = ""  # chat, task, approval, feedback, support
    summary: str = ""
    sentiment: str = "neutral"  # positive, neutral, negative
    topics: list[str] = field(default_factory=list)
    satisfaction_score: float = 0.5  # 0-1
    follow_up_needed: bool = False
    follow_up_note: str = ""
    agent_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "interaction_type": self.interaction_type,
            "summary": self.summary,
            "sentiment": self.sentiment,
            "topics": self.topics,
            "satisfaction_score": self.satisfaction_score,
            "timestamp": self.timestamp,
        }


@dataclass
class UserRelationship:
    user_id: str
    user_name: str = ""
    trust_level: float = 0.5  # 0-1
    interaction_count: int = 0
    avg_satisfaction: float = 0.5
    topics: list[str] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    first_seen: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_seen: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "trust_level": self.trust_level,
            "interaction_count": self.interaction_count,
            "avg_satisfaction": self.avg_satisfaction,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
        }


class UserRelationshipMemory:
    """Manages user interactions and relationship tracking."""

    def __init__(self, store=None):
        self.store = store
        self.relationships: dict[str, UserRelationship] = {}
        self.interactions: dict[str, UserInteraction] = {}
        self._user_interactions: dict[str, list[str]] = {}

    def store_interaction(self, user_id: str, user_name: str = "",
                          interaction_type: str = "chat", summary: str = "",
                          sentiment: str = "neutral", topics: list[str] = None,
                          satisfaction_score: float = 0.5, agent_id: str = None,
                          follow_up_needed: bool = False,
                          follow_up_note: str = "") -> UserInteraction:
        interaction = UserInteraction(
            user_id=user_id,
            user_name=user_name,
            interaction_type=interaction_type,
            summary=summary,
            sentiment=sentiment,
            topics=topics or [],
            satisfaction_score=satisfaction_score,
            follow_up_needed=follow_up_needed,
            follow_up_note=follow_up_note,
            agent_id=agent_id,
        )
        self.interactions[interaction.id] = interaction

        if user_id not in self._user_interactions:
            self._user_interactions[user_id] = []
        self._user_interactions[user_id].append(interaction.id)

        self._update_relationship(interaction)

        if self.store:
            from memory_engine.stores.sqlite_store import MemoryRecord
            record = MemoryRecord(
                memory_type="user_interaction",
                content=f"{interaction_type} with {user_name}: {summary}",
                context={"user_id": user_id, "sentiment": sentiment},
                importance=satisfaction_score,
                tags=topics or [],
                agent_id=agent_id,
                metadata={"interaction_id": interaction.id},
            )
            self.store.store(record)

        return interaction

    def get_history(self, user_id: str, limit: int = 50) -> list[UserInteraction]:
        interaction_ids = self._user_interactions.get(user_id, [])
        interactions = [
            self.interactions[iid]
            for iid in interaction_ids[-limit:]
            if iid in self.interactions
        ]
        return interactions

    def get_relationship(self, user_id: str) -> Optional[UserRelationship]:
        return self.relationships.get(user_id)

    def get_all_relationships(self, min_trust: float = 0.0) -> list[UserRelationship]:
        rels = list(self.relationships.values())
        if min_trust > 0:
            rels = [r for r in rels if r.trust_level >= min_trust]
        return rels

    def _update_relationship(self, interaction: UserInteraction):
        user_id = interaction.user_id
        if user_id not in self.relationships:
            self.relationships[user_id] = UserRelationship(
                user_id=user_id,
                user_name=interaction.user_name,
            )

        rel = self.relationships[user_id]
        rel.interaction_count += 1
        rel.last_seen = interaction.timestamp
        rel.user_name = interaction.user_name or rel.user_name

        total = rel.interaction_count
        rel.avg_satisfaction = (
            (rel.avg_satisfaction * (total - 1) + interaction.satisfaction_score) / total
        )

        if interaction.sentiment == "positive":
            rel.trust_level = min(1.0, rel.trust_level + 0.05)
        elif interaction.sentiment == "negative":
            rel.trust_level = max(0.0, rel.trust_level - 0.1)

        for topic in interaction.topics:
            if topic not in rel.topics:
                rel.topics.append(topic)

    def get_pending_follow_ups(self) -> list[UserInteraction]:
        return [
            i for i in self.interactions.values()
            if i.follow_up_needed
        ]

    def get_user_summary(self, user_id: str) -> dict:
        rel = self.relationships.get(user_id)
        interactions = self.get_history(user_id)
        if not rel:
            return {"user_id": user_id, "known": False}
        return {
            "user_id": user_id,
            "user_name": rel.user_name,
            "trust_level": rel.trust_level,
            "interaction_count": rel.interaction_count,
            "avg_satisfaction": rel.avg_satisfaction,
            "recent_topics": rel.topics[-10:],
            "recent_sentiment": interactions[-1].sentiment if interactions else "unknown",
        }

    def get_stats(self) -> dict:
        rels = list(self.relationships.values())
        interactions = list(self.interactions.values())
        return {
            "total_users": len(rels),
            "total_interactions": len(interactions),
            "avg_trust": sum(r.trust_level for r in rels) / len(rels) if rels else 0,
            "pending_follow_ups": len(self.get_pending_follow_ups()),
        }
