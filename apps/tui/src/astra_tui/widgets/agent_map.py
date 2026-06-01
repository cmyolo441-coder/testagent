"""Agent Map Widget — Agent visualization and network display"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentNode:
    id: str = ""
    name: str = ""
    role: str = ""
    status: str = "idle"
    position_x: float = 0.0
    position_y: float = 0.0
    connections: list[str] = field(default_factory=list)
    performance: float = 0.8
    current_task: str = ""


class AgentMap:
    """Agent visualization widget showing spatial layout and connections."""

    def __init__(self, width: int = 60, height: int = 20):
        self.width = width
        self.height = height
        self.agents: dict[str, AgentNode] = {}
        self.selected_id: Optional[str] = None
        self.show_connections: bool = True
        self.show_labels: bool = True

    def add_agent(self, name: str, role: str = "executor",
                  x: float = None, y: float = None) -> AgentNode:
        agent_id = f"AGT-{len(self.agents) + 1:04d}"
        ax = x if x is not None else (len(self.agents) % 5 + 1) * (self.width / 6)
        ay = y if y is not None else (len(self.agents) // 5 + 1) * (self.height / 4)
        node = AgentNode(
            id=agent_id,
            name=name,
            role=role,
            position_x=ax,
            position_y=ay,
        )
        self.agents[agent_id] = node
        return node

    def connect(self, id_a: str, id_b: str) -> bool:
        a = self.agents.get(id_a)
        b = self.agents.get(id_b)
        if not a or not b:
            return False
        if id_b not in a.connections:
            a.connections.append(id_b)
        if id_a not in b.connections:
            b.connections.append(id_a)
        return True

    def update_status(self, agent_id: str, status: str) -> bool:
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        agent.status = status
        return True

    def get_nearest_agent(self, x: float, y: float) -> Optional[AgentNode]:
        if not self.agents:
            return None
        return min(
            self.agents.values(),
            key=lambda a: ((a.position_x - x) ** 2 + (a.position_y - y) ** 2) ** 0.5,
        )

    def render_ascii(self) -> str:
        grid = [[" " for _ in range(self.width)] for _ in range(self.height)]

        status_chars = {"working": "W", "idle": "I", "waiting": "V", "offline": "O", "error": "X"}

        for agent in self.agents.values():
            gx = int(agent.position_x) % self.width
            gy = int(agent.position_y) % self.height
            char = status_chars.get(agent.status, "?")[0]
            if 0 <= gx < self.width and 0 <= gy < self.height:
                grid[gy][gx] = char

        lines = ["".join(row) for row in grid]
        return "\n".join(lines)

    def render_compact(self) -> str:
        lines = ["┌─ Agent Map ─────────────────────────────────────────┐"]
        status_icons = {"working": "●", "idle": "○", "waiting": "◐", "offline": "○", "error": "✗"}
        for agent in list(self.agents.values())[:8]:
            icon = status_icons.get(agent.status, "?")
            perf = f"{agent.performance:.0%}"
            lines.append(f"│ {icon} {agent.name[:18]:<18} {agent.role:<10} {perf:>5} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_network(self) -> str:
        lines = ["┌─ Agent Network ─────────────────────────────────────┐"]
        for agent in list(self.agents.values())[:5]:
            conns = len(agent.connections)
            conn_names = []
            for cid in agent.connections[:3]:
                c = self.agents.get(cid)
                if c:
                    conn_names.append(c.name[:8])
            conn_str = ", ".join(conn_names) if conn_names else "none"
            lines.append(f"│ {agent.name[:12]:<12} → {conn_str:<30} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render(self) -> str:
        parts = [self.render_compact(), "", self.render_network()]
        return "\n".join(parts)

    def get_stats(self) -> dict:
        agents = list(self.agents.values())
        total_connections = sum(len(a.connections) for a in agents) // 2
        by_status = {}
        for a in agents:
            by_status[a.status] = by_status.get(a.status, 0) + 1
        return {
            "total_agents": len(agents),
            "total_connections": total_connections,
            "by_status": by_status,
            "avg_performance": sum(a.performance for a in agents) / len(agents) if agents else 0,
        }
