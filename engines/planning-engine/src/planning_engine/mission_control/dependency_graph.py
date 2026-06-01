"""Dependency Graph — Task dependency management with cycle detection"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class DependencyType(Enum):
    FINISH_TO_START = "fs"  # Default: B starts after A finishes
    START_TO_START = "ss"   # B starts when A starts
    FINISH_TO_FINISH = "ff" # B finishes when A finishes
    START_TO_FINISH = "sf"  # B finishes when A starts


@dataclass
class Dependency:
    source_id: str
    target_id: str
    dep_type: DependencyType = DependencyType.FINISH_TO_START
    lag: int = 0  # days


class DependencyGraph:
    """Directed acyclic graph for task dependencies."""

    def __init__(self):
        self.edges: dict[str, list[Dependency]] = {}
        self.reverse_edges: dict[str, list[Dependency]] = {}
        self.nodes: set[str] = set()

    def add_node(self, node_id: str):
        self.nodes.add(node_id)
        if node_id not in self.edges:
            self.edges[node_id] = []
        if node_id not in self.reverse_edges:
            self.reverse_edges[node_id] = []

    def add_dependency(self, dep: Dependency):
        self.add_node(dep.source_id)
        self.add_node(dep.target_id)
        self.edges[dep.source_id].append(dep)
        self.reverse_edges[dep.target_id].append(dep)

        if self._has_cycle():
            self.edges[dep.source_id].pop()
            self.reverse_edges[dep.target_id].pop()
            raise ValueError(f"Adding dependency {dep.source_id} -> {dep.target_id} creates a cycle")

    def _has_cycle(self) -> bool:
        visited = set()
        rec_stack = set()

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            for dep in self.edges.get(node, []):
                if dep.target_id not in visited:
                    if dfs(dep.target_id):
                        return True
                elif dep.target_id in rec_stack:
                    return True
            rec_stack.discard(node)
            return False

        for node in self.nodes:
            if node not in visited:
                if dfs(node):
                    return True
        return False

    def topological_sort(self) -> list[str]:
        visited = set()
        order = []

        def dfs(node):
            visited.add(node)
            for dep in self.edges.get(node, []):
                if dep.target_id not in visited:
                    dfs(dep.target_id)
            order.append(node)

        for node in self.nodes:
            if node not in visited:
                dfs(node)

        return list(reversed(order))

    def get_critical_path(self, durations: dict[str, int]) -> list[str]:
        """Find critical path using longest path algorithm."""
        topo = self.topological_sort()
        earliest_start = {n: 0 for n in self.nodes}
        predecessor = {n: None for n in self.nodes}

        for node in topo:
            for dep in self.edges.get(node, []):
                new_start = earliest_start[node] + durations.get(node, 1) + dep.lag
                if new_start > earliest_start[dep.target_id]:
                    earliest_start[dep.target_id] = new_start
                    predecessor[dep.target_id] = node

        end_node = max(self.nodes, key=lambda n: earliest_start[n] + durations.get(n, 1))
        path = []
        current = end_node
        while current is not None:
            path.append(current)
            current = predecessor[current]
        return list(reversed(path))

    def get_dependents(self, node_id: str) -> list[str]:
        return [dep.target_id for dep in self.edges.get(node_id, [])]

    def get_dependencies(self, node_id: str) -> list[str]:
        return [dep.source_id for dep in self.reverse_edges.get(node_id, [])]

    def get_unblocked_nodes(self, completed: set[str]) -> list[str]:
        unblocked = []
        for node in self.nodes:
            if node in completed:
                continue
            deps = self.get_dependencies(node)
            if all(d in completed for d in deps):
                unblocked.append(node)
        return unblocked
