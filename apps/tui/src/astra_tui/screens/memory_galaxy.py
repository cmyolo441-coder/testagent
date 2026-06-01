"""Memory Galaxy Screen — Memory browser and graph visualization"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class MemoryNode:
    id: str = ""
    title: str = ""
    memory_type: str = ""  # episodic, semantic, procedural, working
    content: str = ""
    importance: float = 0.5
    confidence: float = 0.5
    tags: list[str] = field(default_factory=list)
    connections: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_accessed: Optional[str] = None


@dataclass
class MemoryEdge:
    source_id: str = ""
    target_id: str = ""
    relation: str = ""  # related_to, caused_by, part_of, derived_from
    weight: float = 1.0


class MemoryGalaxyScreen:
    """Memory browser and graph visualization screen."""

    TITLE = "Memory Galaxy"

    def __init__(self):
        self.nodes: dict[str, MemoryNode] = {}
        self.edges: list[MemoryEdge] = []
        self.selected_node_id: Optional[str] = None
        self.search_query: str = ""
        self.filter_type: str = ""

    def add_memory(self, title: str, memory_type: str = "episodic",
                   content: str = "", importance: float = 0.5,
                   confidence: float = 0.5, tags: list[str] = None) -> MemoryNode:
        node_id = f"MEM-{len(self.nodes) + 1:04d}"
        node = MemoryNode(
            id=node_id,
            title=title,
            memory_type=memory_type,
            content=content,
            importance=importance,
            confidence=confidence,
            tags=tags or [],
        )
        self.nodes[node_id] = node
        return node

    def connect_memories(self, source_id: str, target_id: str,
                         relation: str = "related_to", weight: float = 1.0) -> bool:
        if source_id not in self.nodes or target_id not in self.nodes:
            return False
        edge = MemoryEdge(
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            weight=weight,
        )
        self.edges.append(edge)
        self.nodes[source_id].connections.append(target_id)
        self.nodes[target_id].connections.append(source_id)
        return True

    def search_memories(self, query: str) -> list[MemoryNode]:
        q = query.lower()
        return [
            n for n in self.nodes.values()
            if q in n.title.lower() or q in n.content.lower() or q in " ".join(n.tags).lower()
        ]

    def filter_by_type(self, memory_type: str) -> list[MemoryNode]:
        return [n for n in self.nodes.values() if n.memory_type == memory_type]

    def filter_by_importance(self, min_importance: float) -> list[MemoryNode]:
        return [n for n in self.nodes.values() if n.importance >= min_importance]

    def get_connected(self, node_id: str) -> list[MemoryNode]:
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [self.nodes[cid] for cid in node.connections if cid in self.nodes]

    def get_islands(self) -> list[list[str]]:
        visited = set()
        islands = []
        for node_id in self.nodes:
            if node_id not in visited:
                component = []
                stack = [node_id]
                while stack:
                    current = stack.pop()
                    if current in visited:
                        continue
                    visited.add(current)
                    component.append(current)
                    node = self.nodes.get(current)
                    if node:
                        for conn in node.connections:
                            if conn not in visited:
                                stack.append(conn)
                islands.append(component)
        return islands

    def get_type_distribution(self) -> dict[str, int]:
        dist = {}
        for node in self.nodes.values():
            dist[node.memory_type] = dist.get(node.memory_type, 0) + 1
        return dist

    def render_header(self) -> str:
        total = len(self.nodes)
        edges = len(self.edges)
        types = self.get_type_distribution()
        type_str = ", ".join(f"{k}:{v}" for k, v in types.items())
        return f"╔══════════════════════════════════════════════════════════╗\n║ MEMORY GALAXY — {total} memories, {edges} connections{'':<15}║\n║ Types: {type_str[:44]:<44} ║\n╚══════════════════════════════════════════════════════════╝"

    def render_memory_list(self) -> str:
        lines = ["┌─ Memory Nodes ──────────────────────────────────────┐"]
        type_icons = {"episodic": "E", "semantic": "S", "procedural": "P", "working": "W"}
        for node in list(self.nodes.values())[:8]:
            icon = type_icons.get(node.memory_type, "?")
            imp = f"{node.importance:.0%}"
            lines.append(f"│ [{icon}] {node.title[:30]:<30} {imp:>5} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_graph_ascii(self) -> str:
        lines = ["┌─ Memory Graph ──────────────────────────────────────┐"]
        for edge in self.edges[:6]:
            src = self.nodes.get(edge.source_id)
            tgt = self.nodes.get(edge.target_id)
            if src and tgt:
                lines.append(f"│ {src.title[:15]:<15} ──{edge.relation[:8]:<8}── {tgt.title[:15]:<15} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_full(self) -> str:
        parts = [
            self.render_header(),
            "",
            self.render_memory_list(),
            "",
            self.render_graph_ascii(),
        ]
        return "\n".join(parts)

    def get_stats(self) -> dict:
        nodes = list(self.nodes.values())
        return {
            "total_memories": len(nodes),
            "total_edges": len(self.edges),
            "type_distribution": self.get_type_distribution(),
            "avg_importance": sum(n.importance for n in nodes) / len(nodes) if nodes else 0,
            "islands": len(self.get_islands()),
        }
