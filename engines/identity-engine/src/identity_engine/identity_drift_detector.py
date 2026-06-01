"""Identity Drift Detector — Compare current identity to a baseline snapshot."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class IdentitySnapshot:
    id: str = field(default_factory=lambda: f"SNAP-{uuid.uuid4().hex[:10]}")
    taken_at: str = field(default_factory=_now_iso)
    values: list[dict] = field(default_factory=list)  # [{label, priority}]
    style: dict = field(default_factory=dict)
    mission_statement: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "taken_at": self.taken_at,
            "values": list(self.values),
            "style": dict(self.style),
            "mission_statement": self.mission_statement,
            "metadata": dict(self.metadata),
        }


@dataclass
class DriftReport:
    baseline_id: str
    current_id: str
    overall_score: float  # 0.0 (no drift) - 1.0 (total drift)
    per_dimension: dict = field(default_factory=dict)
    added_values: list[str] = field(default_factory=list)
    removed_values: list[str] = field(default_factory=list)
    repriorities: list[dict] = field(default_factory=list)
    style_changes: dict = field(default_factory=dict)
    mission_changed: bool = False
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "baseline_id": self.baseline_id,
            "current_id": self.current_id,
            "overall_score": self.overall_score,
            "per_dimension": dict(self.per_dimension),
            "added_values": list(self.added_values),
            "removed_values": list(self.removed_values),
            "repriorities": list(self.repriorities),
            "style_changes": dict(self.style_changes),
            "mission_changed": self.mission_changed,
            "generated_at": self.generated_at,
        }


def _values_to_map(values: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for v in values or []:
        label = str(v.get("label", "")).strip().lower()
        if not label:
            continue
        out[label] = int(v.get("priority", 0))
    return out


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


class IdentityDriftDetector:
    """Compute per-dimension drift between a baseline and current snapshot."""

    NUMERIC_STYLE_FIELDS = {"formality", "verbosity"}
    CATEGORICAL_STYLE_FIELDS = {"tone", "language_preference", "technical_depth", "emoji_allowed"}

    def __init__(self):
        self.baseline: Optional[IdentitySnapshot] = None

    def set_baseline(self, snapshot: IdentitySnapshot) -> None:
        self.baseline = snapshot

    def _values_drift(self, base: dict[str, int], cur: dict[str, int]) -> tuple[float, dict]:
        base_keys = set(base.keys())
        cur_keys = set(cur.keys())
        added = sorted(cur_keys - base_keys)
        removed = sorted(base_keys - cur_keys)

        shared = base_keys & cur_keys
        repriorities = []
        prio_delta_sum = 0.0
        max_prio = max(
            [abs(p) for p in list(base.values()) + list(cur.values())] + [1]
        )
        for k in shared:
            if base[k] != cur[k]:
                repriorities.append({"label": k, "before": base[k], "after": cur[k]})
                prio_delta_sum += abs(base[k] - cur[k]) / max_prio

        churn = len(added) + len(removed)
        total_universe = max(1, len(base_keys | cur_keys))
        churn_score = churn / total_universe
        reprio_score = prio_delta_sum / max(1, len(shared)) if shared else 0.0
        score = _clamp01(0.6 * churn_score + 0.4 * reprio_score)

        return score, {
            "added": added,
            "removed": removed,
            "repriorities": repriorities,
            "churn_score": round(churn_score, 4),
            "reprio_score": round(reprio_score, 4),
        }

    def _style_drift(self, base: dict, cur: dict) -> tuple[float, dict]:
        changes: dict = {}
        numeric_deltas: list[float] = []
        categorical_changes = 0
        categorical_total = 0

        for f in self.NUMERIC_STYLE_FIELDS:
            b = float(base.get(f, 0.0) or 0.0)
            c = float(cur.get(f, 0.0) or 0.0)
            d = abs(c - b)
            numeric_deltas.append(d)
            if d > 1e-9:
                changes[f] = {"before": b, "after": c, "delta": round(d, 4)}

        for f in self.CATEGORICAL_STYLE_FIELDS:
            if f in base or f in cur:
                categorical_total += 1
                if base.get(f) != cur.get(f):
                    categorical_changes += 1
                    changes[f] = {"before": base.get(f), "after": cur.get(f)}

        numeric_score = sum(numeric_deltas) / max(1, len(numeric_deltas))
        categorical_score = (
            categorical_changes / categorical_total if categorical_total else 0.0
        )
        score = _clamp01(0.5 * numeric_score + 0.5 * categorical_score)
        return score, changes

    def _mission_drift(self, base: str, cur: str) -> tuple[float, bool]:
        b = (base or "").strip().lower()
        c = (cur or "").strip().lower()
        if b == c:
            return 0.0, False
        if not b or not c:
            return 1.0, True
        b_toks = set(b.split())
        c_toks = set(c.split())
        jacc = len(b_toks & c_toks) / max(1, len(b_toks | c_toks))
        return _clamp01(1.0 - jacc), True

    def compare(self, current: IdentitySnapshot,
                baseline: Optional[IdentitySnapshot] = None) -> DriftReport:
        base_snap = baseline or self.baseline
        if base_snap is None:
            raise ValueError("No baseline snapshot provided or set.")

        base_vals = _values_to_map(base_snap.values)
        cur_vals = _values_to_map(current.values)
        vals_score, vals_detail = self._values_drift(base_vals, cur_vals)
        style_score, style_changes = self._style_drift(base_snap.style, current.style)
        mission_score, mission_changed = self._mission_drift(
            base_snap.mission_statement, current.mission_statement
        )

        per_dim = {
            "values": round(vals_score, 4),
            "style": round(style_score, 4),
            "mission": round(mission_score, 4),
        }
        overall = round(
            0.5 * vals_score + 0.3 * style_score + 0.2 * mission_score, 4
        )

        return DriftReport(
            baseline_id=base_snap.id,
            current_id=current.id,
            overall_score=overall,
            per_dimension=per_dim,
            added_values=vals_detail["added"],
            removed_values=vals_detail["removed"],
            repriorities=vals_detail["repriorities"],
            style_changes=style_changes,
            mission_changed=mission_changed,
        )
