"""Population Manager — Manage agent allocation"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class AgentStatus(Enum):
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    TRAINING = "training"


@dataclass
class AgentAllocation:
    agent_id: str
    role: str
    institution_id: str
    status: AgentStatus = AgentStatus.ACTIVE
    workload: float = 0.0
    tasks_assigned: int = 0
    tasks_completed: int = 0
    allocation_date: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "institution_id": self.institution_id,
            "status": self.status.value,
            "workload": self.workload,
            "tasks_completed": self.tasks_completed,
        }


@dataclass
class PopulationStats:
    total_agents: int = 0
    active_agents: int = 0
    idle_agents: int = 0
    busy_agents: int = 0
    avg_workload: float = 0.0
    by_role: dict = field(default_factory=dict)
    by_institution: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "total_agents": self.total_agents,
            "active_agents": self.active_agents,
            "avg_workload": round(self.avg_workload, 2),
            "by_role": self.by_role,
            "by_institution": self.by_institution,
        }


class PopulationManager:
    """Manage agent populations and allocation across institutions."""

    def __init__(self):
        self.allocations: dict[str, AgentAllocation] = {}
        self.agents: dict[str, dict] = {}
        self.max_agents: int = 100

    def manage_agents(self, agents: list[dict]) -> dict:
        """Manage and allocate agents across institutions."""
        result = {"allocated": 0, "rejected": 0, "errors": []}
        
        for agent in agents:
            agent_id = agent.get("id", f"AGENT-{uuid.uuid4().hex[:8]}")
            
            if len(self.agents) >= self.max_agents:
                result["rejected"] += 1
                result["errors"].append(f"Max agent limit reached for {agent_id}")
                continue
            
            self.agents[agent_id] = agent
            result["allocated"] += 1
        
        result["population_stats"] = self.get_population_stats()
        return result

    def allocate_agent(self, agent_id: str, role: str, institution_id: str) -> Optional[AgentAllocation]:
        """Allocate an agent to an institution with a specific role."""
        if agent_id not in self.agents:
            return None
        
        allocation = AgentAllocation(
            agent_id=agent_id,
            role=role,
            institution_id=institution_id,
        )
        self.allocations[agent_id] = allocation
        return allocation

    def deallocate_agent(self, agent_id: str) -> bool:
        """Remove an agent allocation."""
        if agent_id in self.allocations:
            del self.allocations[agent_id]
            return True
        return False

    def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update an agent's status."""
        if agent_id in self.allocations:
            self.allocations[agent_id].status = status
            return True
        return False

    def get_population_stats(self) -> PopulationStats:
        """Get population statistics."""
        stats = PopulationStats()
        
        all_allocations = list(self.allocations.values())
        stats.total_agents = len(self.agents)
        stats.active_agents = sum(1 for a in all_allocations if a.status == AgentStatus.ACTIVE)
        stats.idle_agents = sum(1 for a in all_allocations if a.status == AgentStatus.IDLE)
        stats.busy_agents = sum(1 for a in all_allocations if a.status == AgentStatus.BUSY)
        
        if all_allocations:
            stats.avg_workload = sum(a.workload for a in all_allocations) / len(all_allocations)
        
        # Count by role
        for alloc in all_allocations:
            stats.by_role[alloc.role] = stats.by_role.get(alloc.role, 0) + 1
            stats.by_institution[alloc.institution_id] = stats.by_institution.get(alloc.institution_id, 0) + 1
        
        return stats

    def find_available_agents(self, role: Optional[str] = None) -> list[dict]:
        """Find agents that are available for assignment."""
        available = []
        for agent_id, allocation in self.allocations.items():
            if allocation.status in [AgentStatus.IDLE, AgentStatus.ACTIVE]:
                if role is None or allocation.role == role:
                    available.append(self.agents.get(agent_id, {}))
        return available

    def get_workload_balance(self) -> dict:
        """Analyze workload balance across agents."""
        if not self.allocations:
            return {"balanced": True, "imbalance_count": 0}
        
        workloads = [a.workload for a in self.allocations.values()]
        avg_workload = sum(workloads) / len(workloads)
        max_deviation = max(abs(w - avg_workload) for w in workloads)
        
        return {
            "balanced": max_deviation < 0.3,
            "avg_workload": round(avg_workload, 2),
            "max_deviation": round(max_deviation, 2),
            "imbalance_count": sum(1 for w in workloads if abs(w - avg_workload) > 0.3),
        }