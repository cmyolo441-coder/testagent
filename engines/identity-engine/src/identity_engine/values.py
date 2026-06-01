"""Value System — Core values and alignment scoring."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Value:
    value_id: str = field(default_factory=lambda: f"VAL-{uuid.uuid4().hex[:8]}")
    label: str = ""
    description: str = ""
    priority: int = 0  # higher = more important
    examples: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "value_id": self.value_id,
            "label": self.label,
            "description": self.description,
            "priority": self.priority,
            "examples": list(self.examples),
            "created_at": self.created_at,
        }


@dataclass
class AlignmentResult:
    score: float  # -1.0 (anti-aligned) to 1.0 (fully aligned)
    supporting_values: list[Value] = field(default_factory=list)
    conflicting_values: list[Value] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "supporting_values": [v.value_id for v in self.supporting_values],
            "conflicting_values": [v.value_id for v in self.conflicting_values],
            "rationale": self.rationale,
        }


class ValueSystem:
    """Maintain a ranked set of values and evaluate action alignment."""

    def __init__(self, values: Optional[list[Value]] = None):
        self.values: dict[str, Value] = {}
        if values:
            for v in values:
                self.add(v)

    def add(self, value: Value) -> str:
        self.values[value.value_id] = value
        return value.value_id

    def remove(self, value_id: str) -> bool:
        return self.values.pop(value_id, None) is not None

    def get(self, value_id: str) -> Optional[Value]:
        return self.values.get(value_id)

    def rank(self, values: Optional[list[Value]] = None) -> list[Value]:
        """Return values sorted by priority (descending)."""
        pool = values if values is not None else list(self.values.values())
        return sorted(pool, key=lambda v: v.priority, reverse=True)

    def _tokens(self, text: str) -> set[str]:
        return {t.strip(".,;:!?").lower() for t in (text or "").split() if t.strip()}

    def check_action_aligned(self, action_descriptor: dict) -> AlignmentResult:
        """Score an action against the value system.

        action_descriptor may include:
          - description (str)
          - tags (list[str])
          - supports (list[str]): value labels claimed to be supported
          - violates (list[str]): value labels the action conflicts with
        """
        desc = (action_descriptor.get("description") or "").lower()
        tags = {t.lower() for t in action_descriptor.get("tags", [])}
        claimed_support = {s.lower() for s in action_descriptor.get("supports", [])}
        claimed_violate = {s.lower() for s in action_descriptor.get("violates", [])}
        tokens = self._tokens(desc) | tags

        supporting: list[Value] = []
        conflicting: list[Value] = []

        for v in self.values.values():
            label = v.label.lower()
            example_tokens: set[str] = set()
            for ex in v.examples:
                example_tokens |= self._tokens(ex)

            supports = (
                label in claimed_support
                or label in tokens
                or bool(example_tokens & tokens)
            )
            violates = label in claimed_violate

            if violates:
                conflicting.append(v)
            elif supports:
                supporting.append(v)

        sup_weight = sum(max(1, v.priority) for v in supporting)
        conf_weight = sum(max(1, v.priority) for v in conflicting)
        total = sup_weight + conf_weight
        score = 0.0 if total == 0 else (sup_weight - conf_weight) / total

        rationale = (
            f"{len(supporting)} supporting (weight={sup_weight}), "
            f"{len(conflicting)} conflicting (weight={conf_weight})"
        )
        return AlignmentResult(
            score=score,
            supporting_values=supporting,
            conflicting_values=conflicting,
            rationale=rationale,
        )

    def to_dict(self) -> dict:
        return {"values": [v.to_dict() for v in self.rank()]}
