"""Knowledge Graph Screen — Knowledge graph visualization"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class KGNode:
    id: str = ""
    label: str = ""
    node_type: str = ""  # entity, concept, document, agent, tool
    properties: dict = field(default_factory=dict)
    importance: float = 0.5
    connections: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class KGEdge:
    source_id: str = ""
    target_id: str = ""
    relation: str = ""  # relates_to, depends_on, created_by, uses, contains
    weight: float = 1.0
    properties: dict = field(default_factory=dict)


@dataclass
class KGQuery:
    query_id: str = ""
    query_text: str = ""
    results: list[dict] = field(default_factory=list)
    execution_time_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class KnowledgeGraphScreen:
    """Knowledge graph visualization screen."""

    TITLE = "Knowledge Graph"

    def __init__(self):
        self.nodes: dict[str, KGNode] = {}
        self.edges: list[KGEdge] = []
        self.queries: list[KGQuery] = []
        self.selected_node_id: Optional[str] = None

    def add_node(self, label: str, node_type: str = "entity",
                 properties: dict = None, importance: float = 0.5) -> KGNode:
        node_id = f"KG-{len(self.nodes) + 1:04d}"
        node = KGNode(
            id=node_id,
            label=label,
            node_type=node_type,
            properties=properties or {},
            importance=importance,
        )
        self.nodes[node_id] = node
        return node

    def add_edge(self, source_id: str, target_id: str, relation: str = "relates_to",
                 weight: float = 1.0, properties: dict = None) -> bool:
        if source_id not in self.nodes or target_id not in self.nodes:
            return False
        edge = KGEdge(
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            weight=weight,
            properties=properties or {},
        )
        self.edges.append(edge)
        self.nodes[source_id].connections.append(target_id)
        self.nodes[target_id].connections.append(source_id)
        return True

    def query_graph(self, query_text: str) -> list[dict]:
        q = query_text.lower()
        results = []
        for node in self.nodes.values():
            if q in node.label.lower() or q in node.node_type:
                results.append({
                    "id": node.id,
                    "label": node.label,
                    "type": node.node_type,
                    "importance": node.importance,
                })
        kg_query = KGQuery(
            query_id=f"QRY-{len(self.queries) + 1:04d}",
            query_text=query_text,
            results=results,
        )
        self.queries.append(kg_query)
        return results

    def get_neighbors(self, node_id: str, depth: int = 1) -> list[KGNode]:
        visited = set()
        result = []
        queue = [(node_id, 0)]
        while queue:
            current_id, current_depth = queue.pop(0)
            if current_id in visited or current_depth > depth:
                continue
            visited.add(current_id)
            node = self.nodes.get(current_id)
            if node:
                result.append(node)
                for conn_id in node.connections:
                    if conn_id not in visited:
                        queue.append((conn_id, current_depth + 1))
        return result

    def find_path(self, start_id: str, end_id: str) -> Optional[list[str]]:
        visited = set()
        queue = [(start_id, [start_id])]
        while queue:
            current_id, path = queue.pop(0)
            if current_id == end_id:
                return path
            if current_id in visited:
                continue
            visited.add(current_id)
            node = self.nodes.get(current_id)
            if node:
                for conn_id in node.connections:
                    if conn_id not in visited:
                        queue.append((conn_id, path + [conn_id]))
        return None

    def get_type_distribution(self) -> dict[str, int]:
        dist = {}
        for node in self.nodes.values():
            dist[node.node_type] = dist.get(node.node_type, 0) + 1
        return dist

    def get_relation_distribution(self) -> dict[str, int]:
        dist = {}
        for edge in self.edges:
            dist[edge.relation] = dist.get(edge.relation, 0) + 1
        return dist

    def get_central_nodes(self, limit: int = 10) -> list[KGNode]:
        return sorted(
            self.nodes.values(),
            key=lambda n: len(n.connections),
            reverse=True,
        )[:limit]

    def render_header(self) -> str:
        node_count = len(self.nodes)
        edge_count = len(self.edges)
        return f"╔══════════════════════════════════════════════════════════╗\n║ KNOWLEDGE GRAPH — {node_count} nodes, {edge_count} edges{'':<22}║\n╚══════════════════════════════════════════════════════════╝"

    def render_nodes(self) -> str:
        lines = ["┌─ Graph Nodes ───────────────────────────────────────┐"]
        type_icons = {"entity": "E", "concept": "C", "document": "D", "agent": "A", "tool": "T"}
        for node in list(self.nodes.values())[:8]:
            icon = type_icons.get(node.node_type, "?")
            conns = len(node.connections)
            lines.append(f"│ [{icon}] {node.label[:28]:<28} {conns:>3} edges │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_central(self) -> str:
        lines = ["┌─ Central Nodes ─────────────────────────────────────┐"]
        for node in self.get_central_nodes(5):
            lines.append(f"│ {node.label[:20]:<20} connections: {len(node.connections):<15} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_full(self) -> str:
        parts = [
            self.render_header(),
            "",
            self.render_nodes(),
            "",
            self.render_central(),
        ]
        return "\n".join(parts)

    def get_stats(self) -> dict:
        nodes = list(self.nodes.values())
        return {
            "total_nodes": len(nodes),
            "total_edges": len(self.edges),
            "type_distribution": self.get_type_distribution(),
            "relation_distribution": self.get_relation_distribution(),
            "avg_connections": sum(len(n.connections) for n in nodes) / len(nodes) if nodes else 0,
            "total_queries": len(self.queries),
        }
