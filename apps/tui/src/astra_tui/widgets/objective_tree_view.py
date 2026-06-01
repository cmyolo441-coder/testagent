"""Objective Tree View Widget — Hierarchical objective display"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ObjectiveNode:
    id: str = ""
    title: str = ""
    description: str = ""
    status: str = "pending"  # pending, in_progress, completed, blocked, failed
    progress: float = 0.0
    priority: str = "medium"
    parent_id: Optional[str] = None
    children_ids: list[str] = field(default_factory=list)
    assignee: str = ""
    tags: list[str] = field(default_factory=list)


class ObjectiveTreeView:
    """Hierarchical tree view for objectives."""

    def __init__(self, root_id: str = "root"):
        self.root_id = root_id
        self.nodes: dict[str, ObjectiveNode] = {}
        self.nodes[root_id] = ObjectiveNode(id=root_id, title="Root")

    def add_objective(self, title: str, parent_id: str = None,
                      description: str = "", status: str = "pending",
                      priority: str = "medium", assignee: str = "",
                      tags: list[str] = None) -> ObjectiveNode:
        obj_id = f"OBJ-{len(self.nodes):04d}"
        node = ObjectiveNode(
            id=obj_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            parent_id=parent_id or self.root_id,
            assignee=assignee,
            tags=tags or [],
        )
        self.nodes[obj_id] = node
        parent = self.nodes.get(node.parent_id)
        if parent:
            parent.children_ids.append(obj_id)
        return node

    def update_status(self, node_id: str, status: str) -> bool:
        node = self.nodes.get(node_id)
        if not node:
            return False
        node.status = status
        if status == "completed":
            node.progress = 100.0
        self._update_parent_progress(node.parent_id)
        return True

    def _update_parent_progress(self, parent_id: str):
        parent = self.nodes.get(parent_id)
        if not parent or not parent.children_ids:
            return
        children = [self.nodes[cid] for cid in parent.children_ids if cid in self.nodes]
        if children:
            parent.progress = sum(c.progress for c in children) / len(children)

    def get_children(self, node_id: str) -> list[ObjectiveNode]:
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [self.nodes[cid] for cid in node.children_ids if cid in self.nodes]

    def get_siblings(self, node_id: str) -> list[ObjectiveNode]:
        node = self.nodes.get(node_id)
        if not node or not node.parent_id:
            return []
        return self.get_children(node.parent_id)

    def get_path_to_root(self, node_id: str) -> list[ObjectiveNode]:
        path = []
        current = self.nodes.get(node_id)
        while current and current.id != self.root_id:
            path.append(current)
            current = self.nodes.get(current.parent_id) if current.parent_id else None
        path.reverse()
        return path

    def get_all_by_status(self, status: str) -> list[ObjectiveNode]:
        return [n for n in self.nodes.values() if n.status == status and n.id != self.root_id]

    def get_overall_progress(self) -> float:
        root = self.nodes.get(self.root_id)
        return root.progress if root else 0.0

    def render_tree(self, node_id: str = None, depth: int = 0, max_depth: int = 5) -> str:
        if depth > max_depth:
            return ""
        nid = node_id or self.root_id
        node = self.nodes.get(nid)
        if not node:
            return ""

        indent = "  " * depth
        status_icons = {
            "pending": "○", "in_progress": "◐", "completed": "●",
            "blocked": "▼", "failed": "✗",
        }
        icon = status_icons.get(node.status, "?")
        prefix = f"{indent}{icon} " if depth > 0 else ""
        lines = [f"{prefix}{node.title} ({node.progress:.0f}%)"]

        for child_id in node.children_ids:
            child_render = self.render_tree(child_id, depth + 1, max_depth)
            if child_render:
                lines.append(child_render)

        return "\n".join(lines)

    def render(self) -> str:
        header = "┌─ Objective Tree ────────────────────────────────────┐"
        tree = self.render_tree()
        tree_lines = tree.split("\n") if tree else ["  (empty)"]
        formatted = [f"│ {line[:50]:<50} │" for line in tree_lines[:12]]
        footer = "└────────────────────────────────────────────────────┘"
        return "\n".join([header] + formatted + [footer])

    def get_stats(self) -> dict:
        nodes = [n for n in self.nodes.values() if n.id != self.root_id]
        by_status = {}
        for n in nodes:
            by_status[n.status] = by_status.get(n.status, 0) + 1
        return {
            "total_objectives": len(nodes),
            "by_status": by_status,
            "overall_progress": self.get_overall_progress(),
        }
