"""Tree of Thought — Explore multiple reasoning branches and select best"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable
import uuid
import heapq


@dataclass
class ThoughtNode:
    id: str = field(default_factory=lambda: f"TN-{uuid.uuid4().hex[:8]}")
    content: str = ""
    parent_id: Optional[str] = None
    children: list[str] = field(default_factory=list)
    score: float = 0.0
    depth: int = 0
    is_terminal: bool = False
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "parent_id": self.parent_id,
            "children": self.children,
            "score": self.score,
            "depth": self.depth,
            "is_terminal": self.is_terminal,
        }


class TreeOfThought:
    """Explore multiple reasoning paths using tree search with scoring."""

    def __init__(self, generator: Optional[Callable] = None,
                 evaluator: Optional[Callable] = None,
                 max_depth: int = 5,
                 branch_factor: int = 3,
                 beam_width: int = 3):
        self.generator = generator or self._default_generator
        self.evaluator = evaluator or self._default_evaluator
        self.max_depth = max_depth
        self.branch_factor = branch_factor
        self.beam_width = beam_width
        self.trees: dict[str, dict[str, ThoughtNode]] = {}
        self.root_ids: dict[str, str] = {}

    def solve(self, problem: str) -> dict:
        tree_id = f"TREE-{uuid.uuid4().hex[:8]}"
        root = ThoughtNode(content=problem, depth=0)
        nodes = {root.id: root}
        self.trees[tree_id] = nodes
        self.root_ids[tree_id] = root.id

        # BFS with beam search
        current_level = [root]
        for depth in range(self.max_depth):
            candidates = []
            for node in current_level:
                if node.is_terminal:
                    continue
                children = self._generate_children(node, tree_id)
                for child in children:
                    score = self._evaluate_node(child, problem)
                    child.score = score
                    candidates.append(child)
            if not candidates:
                break
            # Beam search: keep top beam_width candidates
            candidates.sort(key=lambda n: n.score, reverse=True)
            beam = candidates[:self.beam_width]
            current_level = beam
            # Mark terminals
            for node in beam:
                if node.depth >= self.max_depth - 1:
                    node.is_terminal = True

        # Find best path
        best_path = self._find_best_path(tree_id)
        return {
            "tree_id": tree_id,
            "best_path": [n.to_dict() for n in best_path],
            "best_score": best_path[-1].score if best_path else 0,
            "total_nodes": len(nodes),
            "depths_explored": self.max_depth,
        }

    def solve_bfs(self, problem: str) -> dict:
        return self.solve(problem)

    def solve_dfs(self, problem: str) -> dict:
        tree_id = f"TREE-{uuid.uuid4().hex[:8]}"
        root = ThoughtNode(content=problem, depth=0)
        nodes = {root.id: root}
        self.trees[tree_id] = nodes
        self.root_ids[tree_id] = root.id

        stack = [root]
        while stack:
            node = stack.pop()
            if node.depth >= self.max_depth:
                node.is_terminal = True
                continue
            children = self._generate_children(node, tree_id)
            for child in children:
                child.score = self._evaluate_node(child, problem)
                stack.append(child)

        best_path = self._find_best_path(tree_id)
        return {
            "tree_id": tree_id,
            "best_path": [n.to_dict() for n in best_path],
            "best_score": best_path[-1].score if best_path else 0,
            "total_nodes": len(nodes),
        }

    def backtrack(self, tree_id: str, node_id: str, new_score: float) -> bool:
        nodes = self.trees.get(tree_id, {})
        node = nodes.get(node_id)
        if not node:
            return False
        node.score = new_score
        return True

    def get_tree_stats(self, tree_id: str) -> dict:
        nodes = self.trees.get(tree_id, {})
        if not nodes:
            return {"error": "tree not found"}
        depths = [n.depth for n in nodes.values()]
        scores = [n.score for n in nodes.values()]
        return {
            "total_nodes": len(nodes),
            "max_depth": max(depths) if depths else 0,
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "terminal_nodes": sum(1 for n in nodes.values() if n.is_terminal),
            "leaf_nodes": sum(1 for n in nodes.values() if not n.children),
        }

    def _generate_children(self, parent: ThoughtNode, tree_id: str) -> list[ThoughtNode]:
        nodes = self.trees[tree_id]
        children = []
        for i in range(self.branch_factor):
            child = self.generator(parent, i)
            child.parent_id = parent.id
            child.depth = parent.depth + 1
            nodes[child.id] = child
            parent.children.append(child.id)
            children.append(child)
        return children

    def _evaluate_node(self, node: ThoughtNode, problem: str) -> float:
        return self.evaluator(node, problem)

    def _find_best_path(self, tree_id: str) -> list[ThoughtNode]:
        nodes = self.trees[tree_id]
        root_id = self.root_ids[tree_id]
        terminals = [n for n in nodes.values() if n.is_terminal]
        if not terminals:
            terminals = [n for n in nodes.values() if not n.children]
        if not terminals:
            return []
        best_terminal = max(terminals, key=lambda n: n.score)
        path = []
        current = best_terminal
        while current:
            path.append(current)
            current = nodes.get(current.parent_id)
        return list(reversed(path))

    @staticmethod
    def _default_generator(node: ThoughtNode, index: int) -> ThoughtNode:
        return ThoughtNode(
            content=f"{node.content} -> option {index + 1}",
            depth=node.depth + 1,
        )

    @staticmethod
    def _default_evaluator(node: ThoughtNode, problem: str) -> float:
        import random
        return random.random()
