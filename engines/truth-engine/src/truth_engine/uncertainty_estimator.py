"""Uncertainty Estimator — produces aleatoric/epistemic estimates for a claim
using ensemble disagreement, lexical hedging, and evidence sparsity.
"""
from dataclasses import dataclass
import re

HEDGE_WORDS = {
    "maybe", "perhaps", "possibly", "might", "could", "seems", "appears",
    "suggests", "indicates", "likely", "probably", "around", "roughly",
}


@dataclass
class UncertaintyEstimate:
    epistemic: float  # 0-1, due to lack of knowledge
    aleatoric: float  # 0-1, due to inherent randomness
    total: float
    rationale: list[str]


class UncertaintyEstimator:
    def estimate(self, text: str, ensemble: list[str] = None,
                 evidence_count: int = 0) -> UncertaintyEstimate:
        rationale: list[str] = []

        # Lexical hedging
        words = set(re.findall(r"\w+", text.lower()))
        hedges = words & HEDGE_WORDS
        lexical_unc = min(1.0, len(hedges) * 0.2)
        if hedges:
            rationale.append(f"Hedge words: {sorted(hedges)}")

        # Ensemble disagreement
        if ensemble and len(ensemble) > 1:
            unique = len(set(ensemble))
            ensemble_unc = (unique - 1) / max(1, len(ensemble) - 1)
            rationale.append(f"Ensemble disagreement: {unique}/{len(ensemble)} unique outputs")
        else:
            ensemble_unc = 0.3
            rationale.append("No ensemble — assuming moderate epistemic uncertainty")

        # Evidence sparsity
        evidence_unc = max(0.0, 1.0 - evidence_count / 5.0)
        rationale.append(f"Evidence count = {evidence_count} → sparsity {evidence_unc:.2f}")

        epistemic = 0.5 * ensemble_unc + 0.5 * evidence_unc
        aleatoric = lexical_unc
        total = min(1.0, epistemic + 0.5 * aleatoric)

        return UncertaintyEstimate(
            epistemic=round(epistemic, 3),
            aleatoric=round(aleatoric, 3),
            total=round(total, 3),
            rationale=rationale,
        )
