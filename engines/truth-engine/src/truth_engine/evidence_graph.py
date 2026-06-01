"""Evidence Graph — graph of claims, evidence, sources and their support relations.

Supports:
 - add_claim / add_evidence / add_source / link
 - rank claims by aggregated support (recursive)
 - export as adjacency dict
"""
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional
import uuid


@dataclass
class Node:
    id: str
    kind: str          # "claim" | "evidence" | "source"
    label: str
    weight: float = 1.0
    metadata: dict = field(default_factory=dict)


@dataclass
class Edge:
    src: str
    dst: str
    relation: str       # "supports" | "refutes" | "cited_by" | "derives_from"
    weight: float = 1.0


class EvidenceGraph:
    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self._out: dict[str, list[Edge]] = defaultdict(list)
        self._in:  dict[str, list[Edge]] = defaultdict(list)

    def add(self, kind: str, label: str, weight: float = 1.0, **meta) -> str:
        nid = f"{kind[:3].upper()}-{uuid.uuid4().hex[:8]}"
        self.nodes[nid] = Node(id=nid, kind=kind, label=label, weight=weight, metadata=meta)
        return nid

    def add_claim(self, label: str, **meta) -> str:      return self.add("claim", label, **meta)
    def add_evidence(self, label: str, reliability: float = 0.5, **meta) -> str:
        return self.add("evidence", label, weight=reliability, **meta)
    def add_source(self, label: str, reliability: float = 0.5, **meta) -> str:
        return self.add("source", label, weight=reliability, **meta)

    def link(self, src: str, dst: str, relation: str = "supports", weight: float = 1.0) -> None:
        if src not in self.nodes or dst not in self.nodes:
            raise KeyError("Unknown node")
        e = Edge(src=src, dst=dst, relation=relation, weight=weight)
        self.edges.append(e)
        self._out[src].append(e)
        self._in[dst].append(e)

    def support_score(self, claim_id: str) -> float:
        """Sum of supporting-evidence reliability minus refuting evidence."""
        pos, neg = 0.0, 0.0
        for e in self._in.get(claim_id, []):
            n = self.nodes[e.src]
            if e.relation == "supports":  pos += n.weight * e.weight
            elif e.relation == "refutes": neg += n.weight * e.weight
        return pos - neg

    def rank_claims(self) -> list[tuple[str, float]]:
        claims = [n for n in self.nodes.values() if n.kind == "claim"]
        return sorted(((c.id, self.support_score(c.id)) for c in claims),
                      key=lambda x: x[1], reverse=True)

    def to_dict(self) -> dict:
        return {
            "nodes": {k: v.__dict__ for k, v in self.nodes.items()},
            "edges": [e.__dict__ for e in self.edges],
        }
