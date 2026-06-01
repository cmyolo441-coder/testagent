"""BeliefState — key->Belief store with confidence, decay, merge, snapshot, diff"""
from dataclasses import dataclass, field, asdict
from typing import Optional, Any, Callable
from datetime import datetime, timezone
import math
import copy
import uuid


@dataclass
class Belief:
    key: str
    value: Any
    confidence: float = 0.5
    source: str = "unknown"
    evidence: list[str] = field(default_factory=list)
    updated_at: str = ""
    belief_id: str = ""

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc).isoformat()
        if not self.belief_id:
            self.belief_id = f"BELIEF-{uuid.uuid4().hex[:8]}"
        self.confidence = max(0.0, min(1.0, float(self.confidence)))


class BeliefState:
    """Confidence-tracked key/value belief store with decay, merge, snapshot, diff."""

    def __init__(self, decay_half_life_seconds: float = 86400.0):
        self._beliefs: dict[str, Belief] = {}
        self.decay_half_life_seconds = max(1.0, float(decay_half_life_seconds))

    def set(
        self,
        key: str,
        value: Any,
        confidence: float = 0.5,
        source: str = "unknown",
        evidence: Optional[list[str]] = None,
    ) -> Belief:
        belief = Belief(
            key=key,
            value=value,
            confidence=confidence,
            source=source,
            evidence=list(evidence or []),
        )
        self._beliefs[key] = belief
        return belief

    def get(self, key: str, apply_decay: bool = True) -> Optional[Belief]:
        b = self._beliefs.get(key)
        if b is None:
            return None
        if apply_decay:
            decayed = copy.copy(b)
            decayed.confidence = self._decayed_confidence(b)
            return decayed
        return b

    def value_of(self, key: str, default: Any = None) -> Any:
        b = self._beliefs.get(key)
        return b.value if b is not None else default

    def confidence_of(self, key: str, apply_decay: bool = True) -> float:
        b = self._beliefs.get(key)
        if b is None:
            return 0.0
        return self._decayed_confidence(b) if apply_decay else b.confidence

    def keys(self) -> list[str]:
        return list(self._beliefs.keys())

    def all(self, apply_decay: bool = True) -> dict[str, Belief]:
        if not apply_decay:
            return dict(self._beliefs)
        out: dict[str, Belief] = {}
        for k, b in self._beliefs.items():
            decayed = copy.copy(b)
            decayed.confidence = self._decayed_confidence(b)
            out[k] = decayed
        return out

    def delete(self, key: str) -> bool:
        return self._beliefs.pop(key, None) is not None

    def merge(self, other: "BeliefState", policy: str = "highest_confidence") -> dict[str, str]:
        """Merge another BeliefState in. Returns per-key resolution: kept|replaced|added."""
        report: dict[str, str] = {}
        for key, incoming in other._beliefs.items():
            existing = self._beliefs.get(key)
            if existing is None:
                self._beliefs[key] = copy.deepcopy(incoming)
                report[key] = "added"
                continue
            if policy == "highest_confidence":
                inc_conf = self._decayed_confidence(incoming)
                exi_conf = self._decayed_confidence(existing)
                if inc_conf > exi_conf:
                    merged = copy.deepcopy(incoming)
                    merged.evidence = list(dict.fromkeys(existing.evidence + incoming.evidence))
                    self._beliefs[key] = merged
                    report[key] = "replaced"
                else:
                    existing.evidence = list(dict.fromkeys(existing.evidence + incoming.evidence))
                    report[key] = "kept"
            elif policy == "latest":
                if incoming.updated_at >= existing.updated_at:
                    self._beliefs[key] = copy.deepcopy(incoming)
                    report[key] = "replaced"
                else:
                    report[key] = "kept"
            elif policy == "union_evidence":
                existing.evidence = list(dict.fromkeys(existing.evidence + incoming.evidence))
                existing.confidence = max(existing.confidence, incoming.confidence)
                existing.updated_at = datetime.now(timezone.utc).isoformat()
                report[key] = "merged"
            else:
                raise ValueError(f"Unknown merge policy: {policy}")
        return report

    def decay(self, now: Optional[datetime] = None) -> int:
        """Apply decay in-place to stored confidence values. Returns count updated."""
        count = 0
        for b in self._beliefs.values():
            new_conf = self._decayed_confidence(b, now=now)
            if abs(new_conf - b.confidence) > 1e-9:
                b.confidence = new_conf
                count += 1
        return count

    def prune(self, min_confidence: float = 0.05) -> list[str]:
        removed: list[str] = []
        for key in list(self._beliefs.keys()):
            if self._decayed_confidence(self._beliefs[key]) < min_confidence:
                removed.append(key)
                del self._beliefs[key]
        return removed

    def snapshot(self) -> dict:
        return {
            "snapshot_id": f"BSNAP-{uuid.uuid4().hex[:8]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "decay_half_life_seconds": self.decay_half_life_seconds,
            "beliefs": {k: asdict(b) for k, b in self._beliefs.items()},
        }

    def restore(self, snapshot: dict) -> None:
        self._beliefs = {}
        self.decay_half_life_seconds = float(snapshot.get("decay_half_life_seconds", self.decay_half_life_seconds))
        for k, payload in snapshot.get("beliefs", {}).items():
            self._beliefs[k] = Belief(**payload)

    def diff(self, other: "BeliefState") -> dict:
        added = []
        removed = []
        changed = []
        for k, b in other._beliefs.items():
            if k not in self._beliefs:
                added.append(k)
            else:
                a = self._beliefs[k]
                if a.value != b.value or abs(a.confidence - b.confidence) > 1e-6:
                    changed.append({
                        "key": k,
                        "from": {"value": a.value, "confidence": a.confidence},
                        "to": {"value": b.value, "confidence": b.confidence},
                    })
        for k in self._beliefs:
            if k not in other._beliefs:
                removed.append(k)
        return {"added": added, "removed": removed, "changed": changed}

    def filter(self, predicate: Callable[[Belief], bool]) -> list[Belief]:
        return [b for b in self._beliefs.values() if predicate(b)]

    def _decayed_confidence(self, belief: Belief, now: Optional[datetime] = None) -> float:
        try:
            updated = datetime.fromisoformat(belief.updated_at)
        except ValueError:
            return belief.confidence
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        current = now or datetime.now(timezone.utc)
        elapsed = max(0.0, (current - updated).total_seconds())
        decay_factor = math.pow(0.5, elapsed / self.decay_half_life_seconds)
        return round(belief.confidence * decay_factor, 6)

    def __len__(self) -> int:
        return len(self._beliefs)

    def __contains__(self, key: str) -> bool:
        return key in self._beliefs
