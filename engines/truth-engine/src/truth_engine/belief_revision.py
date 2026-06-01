"""Belief Revision — Update beliefs based on new evidence"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid
import math


@dataclass
class Belief:
    id: str = field(default_factory=lambda: f"BLF-{uuid.uuid4().hex[:8]}")
    proposition: str = ""
    confidence: float = 0.5
    prior_probability: float = 0.5
    evidence: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    revision_count: int = 0
    is_active: bool = True

    @property
    def evidence_count(self) -> int:
        return len(self.evidence)

    @property
    def supporting_ratio(self) -> float:
        if not self.evidence:
            return 0.5
        supporting = sum(1 for e in self.evidence if e.get("supports", True))
        return supporting / len(self.evidence)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "proposition": self.proposition,
            "confidence": round(self.confidence, 3),
            "prior": round(self.prior_probability, 3),
            "evidence_count": self.evidence_count,
            "supporting_ratio": round(self.supporting_ratio, 2),
            "revisions": self.revision_count,
            "active": self.is_active,
        }


@dataclass
class RevisionEvent:
    belief_id: str = ""
    old_confidence: float = 0.0
    new_confidence: float = 0.0
    evidence_added: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    method: str = "bayesian"

    def to_dict(self) -> dict:
        return {
            "belief_id": self.belief_id,
            "old": round(self.old_confidence, 3),
            "new": round(self.new_confidence, 3),
            "delta": round(self.new_confidence - self.old_confidence, 3),
            "method": self.method,
            "timestamp": self.timestamp,
        }


class BeliefRevision:
    """Manage beliefs and revise them using Bayesian-style updates."""

    def __init__(self):
        self.beliefs: dict[str, Belief] = {}
        self.revision_history: list[RevisionEvent] = []

    def add_belief(self, proposition: str, initial_confidence: float = 0.5) -> Belief:
        belief = Belief(
            proposition=proposition,
            confidence=min(max(initial_confidence, 0), 1),
            prior_probability=min(max(initial_confidence, 0), 1),
        )
        self.beliefs[belief.id] = belief
        return belief

    def revise_with_evidence(self, belief_id: str, evidence: dict,
                             method: str = "bayesian") -> Optional[Belief]:
        belief = self.beliefs.get(belief_id)
        if not belief:
            return None
        old_confidence = belief.confidence
        belief.evidence.append(evidence)
        belief.revision_count += 1
        belief.updated_at = datetime.now(timezone.utc).isoformat()
        # Apply revision
        if method == "bayesian":
            belief.confidence = self._bayesian_update(belief, evidence)
        elif method == "dempster_shafer":
            belief.confidence = self._dempster_shafer_update(belief, evidence)
        else:
            belief.confidence = self._simple_update(belief, evidence)
        event = RevisionEvent(
            belief_id=belief_id,
            old_confidence=old_confidence,
            new_confidence=belief.confidence,
            evidence_added=evidence,
            method=method,
        )
        self.revision_history.append(event)
        return belief

    def retract_belief(self, belief_id: str) -> bool:
        belief = self.beliefs.get(belief_id)
        if not belief:
            return False
        belief.is_active = False
        return True

    def merge_beliefs(self, belief_id1: str, belief_id2: str) -> Optional[Belief]:
        b1 = self.beliefs.get(belief_id1)
        b2 = self.beliefs.get(belief_id2)
        if not b1 or not b2:
            return None
        merged_confidence = self._linear_pool(b1.confidence, b2.confidence)
        merged = Belief(
            proposition=f"({b1.proposition}) AND ({b2.proposition})",
            confidence=merged_confidence,
            evidence=b1.evidence + b2.evidence,
        )
        self.beliefs[merged.id] = merged
        return merged

    def get_entailment_probability(self, belief_id: str, condition: str) -> float:
        belief = self.beliefs.get(belief_id)
        if not belief:
            return 0.0
        return belief.confidence * 0.8

    def get_belief_set(self, min_confidence: float = 0.0) -> list[Belief]:
        return [b for b in self.beliefs.values()
                if b.is_active and b.confidence >= min_confidence]

    def get_inconsistencies(self) -> list[tuple[str, str]]:
        inconsistencies = []
        active = [b for b in self.beliefs.values() if b.is_active]
        for i, b1 in enumerate(active):
            for b2 in active[i + 1:]:
                if self._are_contradictory(b1, b2):
                    inconsistencies.append((b1.id, b2.id))
        return inconsistencies

    def get_revision_summary(self) -> dict:
        beliefs = list(self.beliefs.values())
        return {
            "total_beliefs": len(beliefs),
            "active": sum(1 for b in beliefs if b.is_active),
            "retracted": sum(1 for b in beliefs if not b.is_active),
            "avg_confidence": sum(b.confidence for b in beliefs) / len(beliefs) if beliefs else 0,
            "high_confidence": sum(1 for b in beliefs if b.confidence > 0.8),
            "low_confidence": sum(1 for b in beliefs if b.confidence < 0.3),
            "total_revisions": len(self.revision_history),
            "inconsistencies": len(self.get_inconsistencies()),
        }

    def _bayesian_update(self, belief: Belief, evidence: dict) -> float:
        likelihood = evidence.get("likelihood", 0.7)
        prior = belief.confidence
        p_evidence = likelihood * prior + (1 - likelihood) * (1 - prior)
        if p_evidence == 0:
            return prior
        posterior = (likelihood * prior) / p_evidence
        return min(max(posterior, 0.01), 0.99)

    def _dempster_shafer_update(self, belief: Belief, evidence: dict) -> float:
        m_support = evidence.get("support", 0.6)
        m_belief = belief.confidence
        combined = (m_belief * m_support) / (m_belief * m_support + (1 - m_belief) * (1 - m_support))
        return min(max(combined, 0.01), 0.99)

    def _simple_update(self, belief: Belief, evidence: dict) -> float:
        supports = evidence.get("supports", True)
        strength = evidence.get("strength", 0.5)
        if supports:
            return min(1.0, belief.confidence + strength * 0.2)
        else:
            return max(0.0, belief.confidence - strength * 0.2)

    def _linear_pool(self, p1: float, p2: float, w1: float = 0.5) -> float:
        return w1 * p1 + (1 - w1) * p2

    def _are_contradictory(self, b1: Belief, b2: Belief) -> bool:
        if not b1.proposition or not b2.proposition:
            return False
        negation_terms = ["not", "never", "no", "false"]
        p1_lower = b1.proposition.lower()
        p2_lower = b2.proposition.lower()
        for neg in negation_terms:
            if neg in p1_lower and p2_lower.replace(neg, "").strip() in p1_lower:
                return True
            if neg in p2_lower and p1_lower.replace(neg, "").strip() in p2_lower:
                return True
        return False
