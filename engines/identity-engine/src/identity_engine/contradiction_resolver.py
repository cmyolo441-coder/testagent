"""Contradiction Resolver — Propose resolutions for detected contradictions."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .self_consistency_checker import Contradiction


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


VALID_STRATEGIES = {"retain_newer", "retain_higher_confidence", "escalate_human"}


@dataclass
class Resolution:
    id: str = field(default_factory=lambda: f"RESOL-{uuid.uuid4().hex[:8]}")
    contradiction_subject: str = ""
    strategy: str = "escalate_human"  # retain_newer, retain_higher_confidence, escalate_human
    chosen_statement_id: Optional[str] = None
    rejected_statement_id: Optional[str] = None
    rationale: str = ""
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "contradiction_subject": self.contradiction_subject,
            "strategy": self.strategy,
            "chosen_statement_id": self.chosen_statement_id,
            "rejected_statement_id": self.rejected_statement_id,
            "rationale": self.rationale,
            "created_at": self.created_at,
        }


class ContradictionResolver:
    """Propose resolution strategies for contradictions.

    Heuristic decision rules:
      - confidence < escalation_threshold  -> escalate_human
      - source_confidence supplied per statement -> retain_higher_confidence
      - otherwise -> retain_newer (later timestamp wins)
    """

    def __init__(self, escalation_threshold: float = 0.5):
        self.escalation_threshold = escalation_threshold

    def _statement_confidence(self, statement) -> Optional[float]:
        md = getattr(statement, "metadata", None) or {}
        for key in ("confidence", "source_confidence", "trust"):
            if key in md:
                try:
                    return float(md[key])
                except (TypeError, ValueError):
                    continue
        return None

    def propose(self, contradiction: Contradiction) -> Resolution:
        a = contradiction.stmt_a
        b = contradiction.stmt_b

        # Low overall confidence in the detection -> escalate.
        if contradiction.confidence < self.escalation_threshold:
            return Resolution(
                contradiction_subject=contradiction.subject,
                strategy="escalate_human",
                rationale=(
                    f"Detection confidence {contradiction.confidence:.2f} "
                    f"below escalation threshold {self.escalation_threshold:.2f}."
                ),
            )

        conf_a = self._statement_confidence(a)
        conf_b = self._statement_confidence(b)

        if conf_a is not None and conf_b is not None and conf_a != conf_b:
            chosen, rejected = (a, b) if conf_a > conf_b else (b, a)
            return Resolution(
                contradiction_subject=contradiction.subject,
                strategy="retain_higher_confidence",
                chosen_statement_id=chosen.id,
                rejected_statement_id=rejected.id,
                rationale=(
                    f"Chose statement with higher source confidence "
                    f"({max(conf_a, conf_b):.2f} > {min(conf_a, conf_b):.2f})."
                ),
            )

        # Fall back to newer wins (lexicographic ISO timestamps are time-ordered).
        if a.timestamp == b.timestamp:
            return Resolution(
                contradiction_subject=contradiction.subject,
                strategy="escalate_human",
                rationale="Equal timestamps and no confidence signal; cannot auto-resolve.",
            )
        chosen, rejected = (a, b) if a.timestamp > b.timestamp else (b, a)
        return Resolution(
            contradiction_subject=contradiction.subject,
            strategy="retain_newer",
            chosen_statement_id=chosen.id,
            rejected_statement_id=rejected.id,
            rationale=f"Retained newer statement at {chosen.timestamp}.",
        )

    def propose_all(self, contradictions: list[Contradiction]) -> list[Resolution]:
        return [self.propose(c) for c in contradictions]
