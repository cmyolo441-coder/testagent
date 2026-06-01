"""Agent Civilization Screen — Agent map and status visualization"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Agent:
    id: str = ""
    name: str = ""
    role: str = ""  # planner, executor, reviewer, researcher, architect
    status: str = "idle"  # idle, working, waiting, offline, error
    current_task: Optional[str] = None
    mission_id: Optional[str] = None
    capabilities: list[str] = field(default_factory=list)
    performance_score: float = 0.8
    tasks_completed: int = 0
    tasks_failed: int = 0
    uptime_hours: float = 0.0
    last_active: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    connections: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AgentEvent:
    agent_id: str
    event_type: str = ""  # started_task, completed_task, failed_task, status_change
    description: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentCivilizationScreen:
    """Agent map and status visualization screen."""

    TITLE = "Agent Civilization"

    def __init__(self):
        self.agents: dict[str, Agent] = {}
        self.events: list[AgentEvent] = []
        self.selected_agent_id: Optional[str] = None

    def register_agent(self, name: str, role: str = "executor",
                       capabilities: list[str] = None) -> Agent:
        agent_id = f"AGT-{len(self.agents) + 1:04d}"
        agent = Agent(
            id=agent_id,
            name=name,
            role=role,
            capabilities=capabilities or [],
        )
        self.agents[agent_id] = agent
        self._add_event(agent_id, "registered", f"Agent '{name}' registered as {role}")
        return agent

    def update_agent_status(self, agent_id: str, status: str,
                            current_task: str = None) -> Optional[Agent]:
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        old_status = agent.status
        agent.status = status
        if current_task:
            agent.current_task = current_task
        agent.last_active = datetime.now(timezone.utc).isoformat()
        if old_status != status:
            self._add_event(agent_id, "status_change", f"Status: {old_status} → {status}")
        return agent

    def complete_task(self, agent_id: str, success: bool = True) -> bool:
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        if success:
            agent.tasks_completed += 1
            self._add_event(agent_id, "completed_task", f"Task completed successfully")
        else:
            agent.tasks_failed += 1
            self._add_event(agent_id, "failed_task", f"Task failed")
        agent.current_task = None
        agent.status = "idle"
        return True

    def connect_agents(self, agent_id_a: str, agent_id_b: str) -> bool:
        a = self.agents.get(agent_id_a)
        b = self.agents.get(agent_id_b)
        if not a or not b:
            return False
        if agent_id_b not in a.connections:
            a.connections.append(agent_id_b)
        if agent_id_a not in b.connections:
            b.connections.append(agent_id_a)
        return True

    def get_agents_by_role(self, role: str) -> list[Agent]:
        return [a for a in self.agents.values() if a.role == role]

    def get_agents_by_status(self, status: str) -> list[Agent]:
        return [a for a in self.agents.values() if a.status == status]

    def get_active_agents(self) -> list[Agent]:
        return [a for a in self.agents.values() if a.status in ("working", "waiting")]

    def get_agent_network(self) -> dict[str, list[str]]:
        return {aid: list(a.connections) for aid, a in self.agents.items()}

    def render_header(self) -> str:
        total = len(self.agents)
        active = len(self.get_active_agents())
        return f"╔══════════════════════════════════════════════════════════╗\n║ AGENT CIVILIZATION — {total} agents ({active} active){'':<19}║\n╚══════════════════════════════════════════════════════════╝"

    def render_agent_map(self) -> str:
        lines = ["┌─ Agent Map ─────────────────────────────────────────┐"]
        for agent in list(self.agents.values())[:8]:
            status_icon = {"working": "●", "idle": "○", "waiting": "◐", "offline": "○", "error": "✗"}.get(agent.status, "?")
            score = f"{agent.performance_score:.0%}"
            lines.append(f"│ {status_icon} {agent.name[:18]:<18} {agent.role:<10} {score:>5} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_recent_events(self) -> str:
        lines = ["┌─ Agent Events ──────────────────────────────────────┐"]
        for event in self.events[-5:]:
            lines.append(f"│ {event.timestamp[:16]} {event.agent_id[:10]} {event.event_type:<15} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_full(self) -> str:
        parts = [
            self.render_header(),
            "",
            self.render_agent_map(),
            "",
            self.render_recent_events(),
        ]
        return "\n".join(parts)

    def _add_event(self, agent_id: str, event_type: str, description: str):
        event = AgentEvent(
            agent_id=agent_id,
            event_type=event_type,
            description=description,
        )
        self.events.append(event)

    def get_stats(self) -> dict:
        agents = list(self.agents.values())
        by_role = {}
        by_status = {}
        for a in agents:
            by_role[a.role] = by_role.get(a.role, 0) + 1
            by_status[a.status] = by_status.get(a.status, 0) + 1
        total_completed = sum(a.tasks_completed for a in agents)
        total_failed = sum(a.tasks_failed for a in agents)
        return {
            "total_agents": len(agents),
            "by_role": by_role,
            "by_status": by_status,
            "total_tasks_completed": total_completed,
            "total_tasks_failed": total_failed,
        }
