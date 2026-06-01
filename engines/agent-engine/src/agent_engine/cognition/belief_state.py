"""Belief State — Confidence-weighted knowledge store with decay and merging."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Iterable
import math
import uuid


@dataclass
class Belief:
    id: str = field(default_factory=lambda: f"BELIEF-{uuid.uuid4().hex[:8]}")
    key: str = ""
    value: Any = None
    confidence: float = 0.5
    source: str = "unknown"
    evidence: list[dict] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _parse_iso(ts: str) -> datetime:
    if not ts:
        return datetime.now(timezone.utc)
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return datetime.now(timezone.utc)


class BeliefState:
    """Holds key -> Belief with confidence, evidence trail, decay, merge, and diff."""

    def __init__(self):
        self._beliefs: dict[str, Belief] = {}

    def __contains__(self, key: str) -> bool:
        return key in self._beliefs

    def __len__(self) -> int:
        return len(self._beliefs)

    def keys(self) -> Iterable[str]:
        return self._beliefs.keys()

    def get(self, key: str) -> Optional[Belief]:
        return self._beliefs.get(key)

    def value_of(self, key: str, default: Any = None) -> Any:
        b = self._beliefs.get(key)
        return b.value if b else default

    def assert_(
        self,
        key: str,
        value: Any,
        conf: float = 0.7,
        source: str = "unknown",
        evidence: Optional[list[dict]] = None,
    ) -> Belief:
        conf = _clamp(float(conf))
        now = datetime.now(timezone.utc).isoformat()
        existing = self._beliefs.get(key)
        ev_entry = {
            "value": value,
            "confidence": conf,
            "source": source,
            "ts": now,
            "notes": evidence or [],
        }
        if existing is None:
            belief = Belief(
                key=key,
                value=value,
                confidence=conf,
                source=source,
                evidence=[ev_entry],
                updated_at=now,
                created_at=now,
            )
            self._beliefs[key] = belief
            return belief
        # Merge into existing belief.
        existing.evidence.append(ev_entry)
        # Keep evidence bounded.
        if len(existing.evidence) > 50:
            existing.evidence = existing.evidence[-50:]
        if value == existing.value:
            # Reinforcement: confidence increases but never to 1.
            combined = 1.0 - (1.0 - existing.confidence) * (1.0 - conf)
            existing.confidence = _clamp(combined)
        else:
            if conf > existing.confidence:
                existing.value = value
                existing.confidence = conf
                existing.source = source
            else:
                # Conflicting weaker evidence reduces confidence slightly.
                existing.confidence = _clamp(existing.confidence - (conf * 0.25))
        existing.updated_at = now
        return existing

    def retract(self, key: str) -> bool:
        return self._beliefs.pop(key, None) is not None

    def merge(self, other: "BeliefState", policy: str = "highest_confidence") -> dict:
        """Merge ``other`` into self. Returns a summary of changes."""
        added = 0
        updated = 0
        kept = 0
        for key, b in other._beliefs.items():
            if key not in self._beliefs:
                # Clone the belief (shallow copy of value, fresh id).
                clone = Belief(
                    key=key,
                    value=b.value,
                    confidence=b.confidence,
                    source=b.source,
                    evidence=list(b.evidence),
                    updated_at=b.updated_at,
                    created_at=b.created_at,
                )
                self._beliefs[key] = clone
                added += 1
                continue
            mine = self._beliefs[key]
            if policy == "highest_confidence":
                if b.confidence > mine.confidence:
                    mine.value = b.value
                    mine.confidence = b.confidence
                    mine.source = b.source
                    mine.evidence.extend(b.evidence)
                    mine.updated_at = datetime.now(timezone.utc).isoformat()
                    updated += 1
                else:
                    kept += 1
            elif policy == "latest":
                if _parse_iso(b.updated_at) > _parse_iso(mine.updated_at):
                    mine.value = b.value
                    mine.confidence = b.confidence
                    mine.source = b.source
                    mine.updated_at = b.updated_at
                    mine.evidence.extend(b.evidence)
                    updated += 1
                else:
                    kept += 1
            elif policy == "average":
                if mine.value == b.value:
                    mine.confidence = _clamp((mine.confidence + b.confidence) / 2.0)
                    mine.evidence.extend(b.evidence)
                    updated += 1
                else:
                    if b.confidence > mine.confidence:
                        mine.value = b.value
                        mine.confidence = _clamp((mine.confidence + b.confidence) / 2.0)
                        mine.source = b.source
                        updated += 1
                    else:
                        kept += 1
            else:
                raise ValueError(f"Unknown merge policy: {policy}")
            # Bound evidence.
            if len(mine.evidence) > 50:
                mine.evidence = mine.evidence[-50:]
        return {"added": added, "updated": updated, "kept": kept, "policy": policy}

    def decay(self, rate: float = 0.01, now_iso: Optional[str] = None) -> int:
        """Exponentially decay confidence proportional to elapsed days since update.

        Returns the number of beliefs touched.
        """
        if rate <= 0:
            return 0
        now_dt = _parse_iso(now_iso) if now_iso else datetime.now(timezone.utc)
        touched = 0
        for b in self._beliefs.values():
            updated_dt = _parse_iso(b.updated_at)
            elapsed_days = max(0.0, (now_dt - updated_dt).total_seconds() / 86400.0)
            if elapsed_days <= 0:
                continue
            factor = math.exp(-rate * elapsed_days)
            new_conf = _clamp(b.confidence * factor)
            if abs(new_conf - b.confidence) > 1e-9:
                b.confidence = new_conf
                touched += 1
        return touched

    def snapshot(self) -> dict:
        return {
            "count": len(self._beliefs),
            "taken_at": datetime.now(timezone.utc).isoformat(),
            "beliefs": {
                k: {
                    "id": b.id,
                    "value": b.value,
                    "confidence": round(b.confidence, 4),
                    "source": b.source,
                    "updated_at": b.updated_at,
                    "evidence_count": len(b.evidence),
                }
                for k, b in self._beliefs.items()
            },
        }

    def diff(self, other: "BeliefState") -> dict:
        added: list[str] = []
        removed: list[str] = []
        changed: list[dict] = []
        for k, b in self._beliefs.items():
            if k not in other._beliefs:
                added.append(k)
            else:
                ob = other._beliefs[k]
                if b.value != ob.value or abs(b.confidence - ob.confidence) > 1e-6:
                    changed.append({
                        "key": k,
                        "self": {"value": b.value, "confidence": round(b.confidence, 4)},
                        "other": {"value": ob.value, "confidence": round(ob.confidence, 4)},
                    })
        for k in other._beliefs:
            if k not in self._beliefs:
                removed.append(k)
        return {"added": added, "removed": removed, "changed": changed}

    def query(self, min_confidence: float = 0.0, source: Optional[str] = None) -> list[Belief]:
        result: list[Belief] = []
        for b in self._beliefs.values():
            if b.confidence < min_confidence:
                continue
            if source is not None and b.source != source:
                continue
            result.append(b)
        return result
