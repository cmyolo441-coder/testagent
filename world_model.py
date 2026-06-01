"""WorldModel — entity/relation graph with prediction helpers"""
from dataclasses import dataclass, field
from typing import Optional, Any, Callable
from datetime import datetime, timezone
import copy
import uuid


@dataclass
class Entity:
    entity_id: str
    name: str
    kind: str = "thing"
    attrs: dict = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now


@dataclass
class Relation:
    relation_id: str
    source: str
    target: str
    kind: str = "related_to"
    attrs: dict = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class WorldModel:
    """Entity-relation graph. Pure dict-based, with neighbor/query/predict helpers."""

    def __init__(self):
        self.entities: dict[str, Entity] = {}
        self.relations: dict[str, Relation] = {}
        self._name_index: dict[str, str] = {}
        self._out_edges: dict[str, list[str]] = {}
        self._in_edges: dict[str, list[str]] = {}

    # ---- Entities ----
    def add_entity(
        self,
        name: str,
        kind: str = "thing",
        attrs: Optional[dict] = None,
        entity_id: Optional[str] = None,
    ) -> Entity:
        if name in self._name_index:
            existing = self.entities[self._name_index[name]]
            if attrs:
                existing.attrs.update(attrs)
            if kind and kind != "thing":
                existing.kind = kind
            existing.updated_at = datetime.now(timezone.utc).isoformat()
            return existing
        eid = entity_id or f"ENT-{uuid.uuid4().hex[:8]}"
        entity = Entity(entity_id=eid, name=name, kind=kind, attrs=dict(attrs or {}))
        self.entities[eid] = entity
        self._name_index[name] = eid
        self._out_edges.setdefault(eid, [])
        self._in_edges.setdefault(eid, [])
        return entity

    def get_entity(self, key: str) -> Optional[Entity]:
        if key in self.entities:
            return self.entities[key]
        if key in self._name_index:
            return self.entities[self._name_index[key]]
        return None

    def remove_entity(self, key: str) -> bool:
        entity = self.get_entity(key)
        if entity is None:
            return False
        eid = entity.entity_id
        for rid in list(self._out_edges.get(eid, [])) + list(self._in_edges.get(eid, [])):
            self.relations.pop(rid, None)
        self._out_edges.pop(eid, None)
        self._in_edges.pop(eid, None)
        self._name_index.pop(entity.name, None)
        self.entities.pop(eid, None)
        # Clean dangling references from other adjacency lists
        for adj in (self._out_edges, self._in_edges):
            for k, lst in adj.items():
                adj[k] = [r for r in lst if r in self.relations]
        return True

    # ---- Relations ----
    def add_relation(
        self,
        source: str,
        target: str,
        kind: str = "related_to",
        attrs: Optional[dict] = None,
    ) -> Relation:
        src = self.get_entity(source) or self.add_entity(source)
        tgt = self.get_entity(target) or self.add_entity(target)
        rid = f"REL-{uuid.uuid4().hex[:8]}"
        rel = Relation(
            relation_id=rid,
            source=src.entity_id,
            target=tgt.entity_id,
            kind=kind,
            attrs=dict(attrs or {}),
        )
        self.relations[rid] = rel
        self._out_edges.setdefault(src.entity_id, []).append(rid)
        self._in_edges.setdefault(tgt.entity_id, []).append(rid)
        return rel

    def remove_relation(self, relation_id: str) -> bool:
        rel = self.relations.pop(relation_id, None)
        if rel is None:
            return False
        if rel.source in self._out_edges:
            self._out_edges[rel.source] = [r for r in self._out_edges[rel.source] if r != relation_id]
        if rel.target in self._in_edges:
            self._in_edges[rel.target] = [r for r in self._in_edges[rel.target] if r != relation_id]
        return True

    # ---- Queries ----
    def neighbors(self, key: str, direction: str = "both", kind: Optional[str] = None) -> list[Entity]:
        entity = self.get_entity(key)
        if entity is None:
            return []
        eid = entity.entity_id
        out_ids: list[str] = []
        if direction in ("out", "both"):
            for rid in self._out_edges.get(eid, []):
                rel = self.relations[rid]
                if kind is None or rel.kind == kind:
                    out_ids.append(rel.target)
        if direction in ("in", "both"):
            for rid in self._in_edges.get(eid, []):
                rel = self.relations[rid]
                if kind is None or rel.kind == kind:
                    out_ids.append(rel.source)
        seen = set()
        result: list[Entity] = []
        for nid in out_ids:
            if nid in seen:
                continue
            seen.add(nid)
            if nid in self.entities:
                result.append(self.entities[nid])
        return result

    def query(
        self,
        kind: Optional[str] = None,
        attrs: Optional[dict] = None,
        predicate: Optional[Callable[[Entity], bool]] = None,
    ) -> list[Entity]:
        results: list[Entity] = []
        for ent in self.entities.values():
            if kind is not None and ent.kind != kind:
                continue
            if attrs:
                ok = True
                for k, v in attrs.items():
                    if ent.attrs.get(k) != v:
                        ok = False
                        break
                if not ok:
                    continue
            if predicate is not None and not predicate(ent):
                continue
            results.append(ent)
        return results

    def relations_of(self, key: str, direction: str = "both", kind: Optional[str] = None) -> list[Relation]:
        entity = self.get_entity(key)
        if entity is None:
            return []
        eid = entity.entity_id
        rids: list[str] = []
        if direction in ("out", "both"):
            rids.extend(self._out_edges.get(eid, []))
        if direction in ("in", "both"):
            rids.extend(self._in_edges.get(eid, []))
        rels = [self.relations[r] for r in rids if r in self.relations]
        if kind is not None:
            rels = [r for r in rels if r.kind == kind]
        return rels

    def path(self, start: str, end: str, max_depth: int = 6) -> list[str]:
        s = self.get_entity(start)
        t = self.get_entity(end)
        if s is None or t is None:
            return []
        if s.entity_id == t.entity_id:
            return [s.entity_id]
        from collections import deque
        queue: deque[tuple[str, list[str]]] = deque([(s.entity_id, [s.entity_id])])
        visited = {s.entity_id}
        while queue:
            node, trail = queue.popleft()
            if len(trail) > max_depth:
                continue
            for rid in self._out_edges.get(node, []) + self._in_edges.get(node, []):
                rel = self.relations[rid]
                nxt = rel.target if rel.source == node else rel.source
                if nxt in visited:
                    continue
                if nxt == t.entity_id:
                    return trail + [nxt]
                visited.add(nxt)
                queue.append((nxt, trail + [nxt]))
        return []

    def predict_state_after(self, action: dict) -> dict:
        """Predict the next snapshot after applying an action_descriptor.

        action keys understood:
          - type: 'add_entity'|'add_relation'|'remove_entity'|'remove_relation'|'set_attr'
          - name|source|target|kind|attrs|relation_id|entity|key|value
        """
        clone = self.clone()
        atype = action.get("type", "noop")
        try:
            if atype == "add_entity":
                clone.add_entity(
                    name=action["name"],
                    kind=action.get("kind", "thing"),
                    attrs=action.get("attrs"),
                )
            elif atype == "add_relation":
                clone.add_relation(
                    source=action["source"],
                    target=action["target"],
                    kind=action.get("kind", "related_to"),
                    attrs=action.get("attrs"),
                )
            elif atype == "remove_entity":
                clone.remove_entity(action["name"])
            elif atype == "remove_relation":
                clone.remove_relation(action["relation_id"])
            elif atype == "set_attr":
                ent = clone.get_entity(action["entity"])
                if ent is not None:
                    ent.attrs[action["key"]] = action["value"]
                    ent.updated_at = datetime.now(timezone.utc).isoformat()
            applied = True
            error: Optional[str] = None
        except Exception as exc:  # noqa: BLE001 — predictor must not crash callers
            applied = False
            error = f"{type(exc).__name__}: {exc}"
        return {
            "applied": applied,
            "error": error,
            "action": action,
            "entity_count": len(clone.entities),
            "relation_count": len(clone.relations),
            "snapshot": clone.snapshot(),
        }

    def clone(self) -> "WorldModel":
        wm = WorldModel()
        wm.entities = {eid: copy.deepcopy(e) for eid, e in self.entities.items()}
        wm.relations = {rid: copy.deepcopy(r) for rid, r in self.relations.items()}
        wm._name_index = dict(self._name_index)
        wm._out_edges = {k: list(v) for k, v in self._out_edges.items()}
        wm._in_edges = {k: list(v) for k, v in self._in_edges.items()}
        return wm

    def snapshot(self) -> dict:
        return {
            "snapshot_id": f"WSNAP-{uuid.uuid4().hex[:8]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "entities": {
                eid: {"name": e.name, "kind": e.kind, "attrs": dict(e.attrs)}
                for eid, e in self.entities.items()
            },
            "relations": {
                rid: {"source": r.source, "target": r.target, "kind": r.kind, "attrs": dict(r.attrs)}
                for rid, r in self.relations.items()
            },
        }

    def stats(self) -> dict:
        kind_counts: dict[str, int] = {}
        for e in self.entities.values():
            kind_counts[e.kind] = kind_counts.get(e.kind, 0) + 1
        rel_kind_counts: dict[str, int] = {}
        for r in self.relations.values():
            rel_kind_counts[r.kind] = rel_kind_counts.get(r.kind, 0) + 1
        return {
            "entities": len(self.entities),
            "relations": len(self.relations),
            "entity_kinds": kind_counts,
            "relation_kinds": rel_kind_counts,
        }
