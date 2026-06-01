"""Graph of Thought — Reasoning with graph-structured thought patterns"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable
from collections import defaultdict
import uuid


@dataclass
class GraphNode:
    id: str = field(default_factory=lambda: f"GN-{uuid.uuid4().hex[:8]}")
    content: str = ""
    node_type: str = "thought"  # thought, fact, inference, conclusion
    score: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "type": self.node_type,
            "score": self.score,
        }


@dataclass
class GraphEdge:
    source_id: str = ""
    target_id: str = ""
    edge_type: str = "implies"  # implies, contradicts, supports, refines
    weight: float = 1.0

    def to_dict(self) -> dict:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.edge_type,
            "weight": self.weight,
        }


class GraphOfThought:
    """Graph-based reasoning with support for convergence, divergence, and loops."""

    def __init__(self, aggregator: Optional[Callable] = None,
                 evaluator: Optional[Callable] = None):
        self.aggregator = aggregator or self._default_aggregator
        self.evaluator = evaluator or self._default_evaluator
        self.graphs: dict[str, dict] = {}
        self._adj: dict[str, dict[str, list[GraphNode]]] = defaultdict(lambda: defaultdict(list))
        self._reverse: dict[str, dict[str, list[GraphNode]]] = defaultdict(lambda: defaultdict(list))

    def create_graph(self, problem: str) -> str:
        graph_id = f"GOT-{uuid.uuid4().hex[:8]}"
        root = GraphNode(content=problem, node_type="thought", score=1.0)
        self.graphs[graph_id] = {
            "problem": problem,
            "nodes": {root.id: root},
            "edges": [],
            "root_id": root.id,
        }
        return graph_id

    def add_thought(self, graph_id: str, content: str, parent_id: str = None,
                    node_type: str = "thought") -> GraphNode:
        graph = self.graphs.get(graph_id)
        if not graph:
            raise ValueError(f"Graph {graph_id} not found")
        node = GraphNode(content=content, node_type=node_type)
        graph["nodes"][node.id] = node
        if parent_id and parent_id in graph["nodes"]:
            edge = GraphEdge(source_id=parent_id, target_id=node.id, edge_type="implies")
            graph["edges"].append(edge)
            self._adj[graph_id][parent_id].append(node)
            self._reverse[graph_id][node.id].append(graph["nodes"][parent_id])
        return node

    def add_relation(self, graph_id: str, source_id: str, target_id: str,
                     relation: str = "implies", weight: float = 1.0) -> bool:
        graph = self.graphs.get(graph_id)
        if not graph:
            return False
        if source_id not in graph["nodes"] or target_id not in graph["nodes"]:
            return False
        edge = GraphEdge(source_id=source_id, target_id=target_id,
                         edge_type=relation, weight=weight)
        graph["edges"].append(edge)
        self._adj[graph_id][source_id].append(graph["nodes"][target_id])
        self._reverse[graph_id][target_id].append(graph["nodes"][source_id])
        return True

    def converge(self, graph_id: str, node_ids: list[str], summary: str) -> GraphNode:
        graph = self.graphs.get(graph_id)
        if not graph:
            raise ValueError(f"Graph {graph_id} not found")
        contents = [graph["nodes"][nid].content for nid in node_ids if nid in graph["nodes"]]
        merged = self.aggregator(contents, summary)
        node = GraphNode(content=merged, node_type="inference", score=0.8)
        graph["nodes"][node.id] = node
        for nid in node_ids:
            if nid in graph["nodes"]:
                edge = GraphEdge(source_id=nid, target_id=node.id, edge_type="converges")
                graph["edges"].append(edge)
        return node

    def diverge(self, graph_id: str, node_id: str, aspects: list[str]) -> list[GraphNode]:
        graph = self.graphs.get(graph_id)
        if not graph or node_id not in graph["nodes"]:
            return []
        nodes = []
        for aspect in aspects:
            node = GraphNode(content=f"{graph['nodes'][node_id].content} -> {aspect}",
                           node_type="thought")
            graph["nodes"][node.id] = node
            edge = GraphEdge(source_id=node_id, target_id=node.id, edge_type="diverges")
            graph["edges"].append(edge)
            nodes.append(node)
        return nodes

    def evaluate_graph(self, graph_id: str) -> dict:
        graph = self.graphs.get(graph_id)
        if not graph:
            return {"error": "graph not found"}
        nodes = graph["nodes"]
        for node in nodes.values():
            node.score = self.evaluator(node, graph["problem"])
        # Propagate scores
        topo = self._topological_sort(graph_id)
        for nid in topo:
            node = nodes[nid]
            incoming = self._reverse[graph_id].get(nid, [])
            if incoming:
                avg_parent = sum(p.score for p in incoming) / len(incoming)
                node.score = 0.7 * node.score + 0.3 * avg_parent
        return {
            "graph_id": graph_id,
            "node_count": len(nodes),
            "edge_count": len(graph["edges"]),
            "avg_score": sum(n.score for n in nodes.values()) / len(nodes) if nodes else 0,
            "top_nodes": sorted(
                [{"id": n.id, "content": n.content[:50], "score": n.score}
                 for n in nodes.values()],
                key=lambda x: x["score"], reverse=True
            )[:5],
        }

    def find_contradictions(self, graph_id: str) -> list[dict]:
        graph = self.graphs.get(graph_id)
        if not graph:
            return []
        contradictions = []
        for edge in graph["edges"]:
            if edge.edge_type == "contradicts":
                contradictions.append({
                    "source": graph["nodes"].get(edge.source_id, GraphNode()).content[:50],
                    "target": graph["nodes"].get(edge.target_id, GraphNode()).content[:50],
                })
        return contradictions

    def get_best_path(self, graph_id: str) -> list[GraphNode]:
        graph = self.graphs.get(graph_id)
        if not graph:
            return []
        self.evaluate_graph(graph_id)
        nodes = graph["nodes"]
        conclusion_nodes = [n for n in nodes.values() if n.node_type == "conclusion"]
        if not conclusion_nodes:
            conclusion_nodes = [n for n in nodes.values() if not self._adj[graph_id].get(n.id)]
        if not conclusion_nodes:
            return []
        best = max(conclusion_nodes, key=lambda n: n.score)
        path = []
        current = best
        visited = set()
        while current and current.id not in visited:
            path.append(current)
            visited.add(current.id)
            parents = self._reverse[graph_id].get(current.id, [])
            current = max(parents, key=lambda n: n.score) if parents else None
        return list(reversed(path))

    def get_graph_stats(self, graph_id: str) -> dict:
        graph = self.graphs.get(graph_id)
        if not graph:
            return {"error": "graph not found"}
        type_counts = defaultdict(int)
        for node in graph["nodes"].values():
            type_counts[node.node_type] += 1
        edge_types = defaultdict(int)
        for edge in graph["edges"]:
            edge_types[edge.edge_type] += 1
        return {
            "nodes": len(graph["nodes"]),
            "edges": len(graph["edges"]),
            "by_type": dict(type_counts),
            "edge_types": dict(edge_types),
        }

    def _topological_sort(self, graph_id: str) -> list[str]:
        graph = self.graphs.get(graph_id, {})
        nodes = graph.get("nodes", {})
        adj = defaultdict(list)
        for edge in graph.get("edges", []):
            adj[edge.source_id].append(edge.target_id)
        visited = set()
        order = []
        def dfs(node_id):
            visited.add(node_id)
            for neighbor in adj.get(node_id, []):
                if neighbor not in visited:
                    dfs(neighbor)
            order.append(node_id)
        for nid in nodes:
            if nid not in visited:
                dfs(nid)
        return order

    @staticmethod
    def _default_aggregator(contents: list[str], summary: str) -> str:
        return f"Merged: {'; '.join(c[:30] for c in contents[:3])}"

    @staticmethod
    def _default_evaluator(node: GraphNode, problem: str) -> float:
        import random
        return 0.3 + random.random() * 0.5
