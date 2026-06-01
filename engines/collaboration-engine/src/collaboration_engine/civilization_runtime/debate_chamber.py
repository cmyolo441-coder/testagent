"""Debate Chamber — Facilitate structured debates"""
from dataclasses import dataclass, field
from typing import Optional
import uuid
from datetime import datetime


@dataclass
class DebateArgument:
    agent_id: str
    position: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    supporting_evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"agent_id": self.agent_id, "position": self.position, "content": self.content}


@dataclass
class DebateRecord:
    id: str = field(default_factory=lambda: f"DEBATE-{uuid.uuid4().hex[:8]}")
    topic: str = ""
    participants: list[str] = field(default_factory=list)
    arguments: list[DebateArgument] = field(default_factory=list)
    status: str = "active"
    outcome: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {"id": self.id, "topic": self.topic, "participants": len(self.participants), "arguments": len(self.arguments), "status": self.status}


class DebateChamber:
    """Facilitate structured debates between agents."""

    def __init__(self):
        self.debates: dict[str, DebateRecord] = {}
        self.argument_count: int = 0

    def debate(self, topic: str, agents: list[str]) -> DebateRecord:
        """Start a new debate on a topic."""
        debate = DebateRecord(topic=topic, participants=agents)
        self.debates[debate.id] = debate
        return debate

    def add_argument(self, debate_id: str, agent_id: str, position: str, content: str, evidence: list[str] = None) -> bool:
        debate = self.debates.get(debate_id)
        if not debate or debate.status != "active":
            return False
        
        argument = DebateArgument(
            agent_id=agent_id,
            position=position,
            content=content,
            supporting_evidence=evidence or [],
        )
        debate.arguments.append(argument)
        self.argument_count += 1
        return True

    def close_debate(self, debate_id: str, outcome: str) -> bool:
        debate = self.debates.get(debate_id)
        if not debate:
            return False
        
        debate.status = "closed"
        debate.outcome = outcome
        return True

    def get_debate_summary(self, debate_id: str) -> dict:
        debate = self.debates.get(debate_id)
        if not debate:
            return {"error": "Debate not found"}
        
        positions = {}
        for arg in debate.arguments:
            pos = arg.position
            if pos not in positions:
                positions[pos] = 0
            positions[pos] += 1
        
        return {
            "debate": debate.to_dict(),
            "argument_distribution": positions,
            "total_arguments": len(debate.arguments),
        }

    def get_debate_stats(self) -> dict:
        return {
            "total_debates": len(self.debates),
            "active_debates": sum(1 for d in self.debates.values() if d.status == "active"),
            "total_arguments": self.argument_count,
        }