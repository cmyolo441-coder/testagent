"""World Model — Typed entity-relation graph with hypothetical state prediction."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Callable
import copy
import uuid


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    attrs: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Relation:
    id: str = field(default_factory=lambda: f"REL-{uuid.uuid4().hex[:8]}")
    src: str = ""
    type: str = "related_to"
    dst: str = ""
    attrs: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# A rule maps an action verb to a function that returns a list of attribute deltas.
# Each delta: {"entity_id": str, "set": {...}} or {"entity_id": str, "delta": {...}}.
RuleFn = Callable[["WorldModel", dict], list[dict]]


def _rule_deploy(world: "WorldModel", action: dict) -> list[dict]:
    target = action.get("target")
    if not target:
        return []
    return [{
        "entity_id": target,
        "set": {"status": "deployed", "last_deploy": datetime.now(timezone.utc).isoformat()},
    }]


def _rule_stop(world: "WorldModel", action: dict) -> list[dict]:
    target = action.get("target")
    if not target:
        return []
    return [{"entity_id": target, "set": {"status": "stopped"}}]


def _rule_start(world: "WorldModel", action: dict) -> list[dict]:
    target = action.get("target")
    if not target:
        return []
    return [{"entity_id": target, "set": {"status": "running"}}]


def _rule_scale(world: "WorldModel", action: dict) -> list[dict]:
    target = action.get("target")
    factor = action.get("factor", 2)
    if not target:
        return []
    ent = world.get(target)
    if not ent:
        return []
    cur = ent.attrs.get("replicas", 1)
    return [{"entity_id": target, "set": {"replicas": max(0, int(cur) * int(factor))}}]


def _rule_delete(world: "WorldModel", action: dict) -> list[dict]:
    target = action.get("target")
    if not target:
        return []
    return [{"entity_id": target, "set": {"status": "deleted", "exists": False}}]


DEFAULT_RULES: dict[str, RuleFn] = {
    "deploy": _rule_deploy,
    "stop": _rule_stop,
    "start": _rule_start,
    "scale": _rule_scale,
    "delete": _rule_delete,
}


class WorldModel:
    """Holds entities and relations; can simulate hypothetical actions."""

    def __init__(self, rules: Optional[dict[str, RuleFn]] = None):
        self.entities: dict[str, Entity] = {}
        self.relations: list[Relation] = []
        self.rules: dict[str, RuleFn] = dict(DEFAULT_RULES)
        if rules:
            self.rules.update(rules)

    # ---------- mutation ----------

    def add_entity(self, id: str, kind: str = "thing", attrs: Optional[dict] = None) -> Entity:
        if id in self.entities:
            ent = self.entities[id]
            if attrs:
                ent.attrs.update(attrs)
            ent.kind = kind or ent.kind
            ent.updated_at = datetime.now(timezone.utc).isoformat()
            return ent
        ent = Entity(id=id, kind=kind, attrs=dict(attrs or {}))
        self.entities[id] = ent
        return ent

    def update_entity(self, id: str, attrs: dict) -> Optional[Entity]:
        ent = self.entities.get(id)
        if not ent:
            return None
        ent.attrs.update(attrs)
        ent.updated_at = datetime.now(timezone.utc).isoformat()
        return ent

    def remove_entity(self, id: str) -> bool:
        if id not in self.entities:
            return False
        del self.entities[id]
        self.relations = [r for r in self.relations if r.src != id and r.dst != id]
        return True

    def add_relation(
        self,
        src: str,
        type: str,
        dst: str,
        attrs: Optional[dict] = None,
    ) -> Relation:
        # Auto-create endpoints if they don't yet exist.
        if src not in self.entities:
            self.add_entity(src)
        if dst not in self.entities:
            self.add_entity(dst)
        rel = Relation(src=src, type=type, dst=dst, attrs=dict(attrs or {}))
        self.relations.append(rel)
        return rel

    # ---------- queries ----------

    def get(self, id: str) -> Optional[Entity]:
        return self.entities.get(id)

    def neighbors(self, id: str, rel: Optional[str] = None) -> list[dict]:
        out: list[dict] = []
        for r in self.relations:
            if r.src == id and (rel is None or r.type == rel):
                ent = self.entities.get(r.dst)
                out.append({
                    "direction": "out",
                    "relation": r.type,
                    "entity": ent,
                    "attrs": r.attrs,
                })
            elif r.dst == id and (rel is None or r.type == rel):
                ent = self.entities.get(r.src)
                out.append({
                    "direction": "in",
                    "relation": r.type,
                    "entity": ent,
                    "attrs": r.attrs,
                })
        return out

    def query(
        self,
        kind: Optional[str] = None,
        attr_filters: Optional[dict] = None,
    ) -> list[Entity]:
        attr_filters = attr_filters or {}
        out: list[Entity] = []
        for ent in self.entities.values():
            if kind is not None and ent.kind != kind:
                continue
            ok = True
            for k, v in attr_filters.items():
                if ent.attrs.get(k) != v:
                    ok = False
                    break
            if ok:
                out.append(ent)
        return out

    # ---------- prediction ----------

    def register_rule(self, action: str, fn: RuleFn) -> None:
        self.rules[action] = fn

    def predict_state_after(self, action_descriptor: dict) -> dict:
        """Predict hypothetical attribute deltas without mutating state."""
        action = action_descriptor.get("action") or action_descriptor.get("verb")
        if not action:
            return {"action": None, "deltas": [], "warnings": ["missing action"]}
        rule = self.rules.get(action)
        if rule is None:
            return {
                "action": action,
                "deltas": [],
                "warnings": [f"no rule registered for action '{action}'"],
            }
        # Operate on a snapshot so prediction is read-only.
        sim = WorldModel(rules=self.rules)
        sim.entities = {k: Entity(id=v.id, kind=v.kind, attrs=copy.deepcopy(v.attrs))
                        for k, v in self.entities.items()}
        sim.relations = [Relation(id=r.id, src=r.src, type=r.type, dst=r.dst,
                                  attrs=copy.deepcopy(r.attrs)) for r in self.relations]
        deltas = rule(sim, action_descriptor)
        # Compute post-state for affected entities.
        post: dict[str, dict] = {}
        for d in deltas:
            eid = d.get("entity_id")
            if not eid:
                continue
            cur = self.entities.get(eid)
            base = copy.deepcopy(cur.attrs) if cur else {}
            if "set" in d:
                base.update(d["set"])
            if "delta" in d:
                for k, v in d["delta"].items():
                    if isinstance(v, (int, float)) and isinstance(base.get(k), (int, float)):
                        base[k] = base[k] + v
                    else:
                        base[k] = v
            post[eid] = base
        return {
            "action": action,
            "descriptor": action_descriptor,
            "deltas": deltas,
            "predicted_state": post,
            "warnings": [],
        }

    def snapshot(self) -> dict:
        return {
            "entities": {
                eid: {"id": e.id, "kind": e.kind, "attrs": e.attrs}
                for eid, e in self.entities.items()
            },
            "relations": [
                {"id": r.id, "src": r.src, "type": r.type, "dst": r.dst, "attrs": r.attrs}
                for r in self.relations
            ],
            "rules": sorted(self.rules.keys()),
            "taken_at": datetime.now(timezone.utc).isoformat(),
        }
