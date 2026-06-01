"""Agent Society — Manage populations of agents"""
from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class AgentRole:
    name: str
    description: str
    skills: list[str] = field(default_factory=list)
    max_agents: int = 10
    current_count: int = 0


@dataclass
class AgentMember:
    id: str = field(default_factory=lambda: f"MEMBER-{uuid.uuid4().hex[:8]}")
    name: str = ""
    role: str = ""
    skills: list[str] = field(default_factory=list)
    reputation: float = 0.5
    active: bool = True
    missions_completed: int = 0
    tasks_completed: int = 0


class AgentSociety:
    """Manage a society of agents with roles and reputation."""

    def __init__(self):
        self.roles: dict[str, AgentRole] = {}
        self.members: dict[str, AgentMember] = {}
        self.interactions: list[dict] = []

    def define_role(self, name: str, description: str, skills: list[str] = None, max_agents: int = 10):
        self.roles[name] = AgentRole(name=name, description=description, skills=skills or [], max_agents=max_agents)

    def add_member(self, name: str, role: str, skills: list[str] = None) -> AgentMember:
        member = AgentMember(name=name, role=role, skills=skills or [])
        self.members[member.id] = member
        return member

    def get_members_by_role(self, role: str) -> list[AgentMember]:
        return [m for m in self.members.values() if m.role == role and m.active]

    def get_top_members(self, n: int = 5) -> list[AgentMember]:
        return sorted(self.members.values(), key=lambda m: m.reputation, reverse=True)[:n]

    def record_interaction(self, agent_a: str, agent_b: str, interaction_type: str, outcome: str):
        self.interactions.append({
            "agent_a": agent_a,
            "agent_b": agent_b,
            "type": interaction_type,
            "outcome": outcome,
        })

    def update_reputation(self, agent_id: str, delta: float):
        member = self.members.get(agent_id)
        if member:
            member.reputation = max(0, min(1, member.reputation + delta))

    def get_stats(self) -> dict:
        active = sum(1 for m in self.members.values() if m.active)
        return {
            "total_members": len(self.members),
            "active_members": active,
            "roles": len(self.roles),
            "interactions": len(self.interactions),
        }
