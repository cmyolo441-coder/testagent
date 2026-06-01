"""Uncertainty Estimator — Beta-distribution success tracking plus ensemble agreement."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import math
import statistics
import uuid


# Two-sided z-scores for common confidence levels.
_Z_SCORES: dict[float, float] = {
    0.80: 1.2816,
    0.90: 1.6449,
    0.95: 1.9600,
    0.975: 2.2414,
    0.99: 2.5758,
}


def _z_for(confidence: float) -> float:
    if confidence in _Z_SCORES:
        return _Z_SCORES[confidence]
    # Linear interpolation between known levels for robustness.
    levels = sorted(_Z_SCORES.keys())
    if confidence <= levels[0]:
        return _Z_SCORES[levels[0]]
    if confidence >= levels[-1]:
        return _Z_SCORES[levels[-1]]
    for lo, hi in zip(levels, levels[1:]):
        if lo <= confidence <= hi:
            frac = (confidence - lo) / (hi - lo)
            return _Z_SCORES[lo] + frac * (_Z_SCORES[hi] - _Z_SCORES[lo])
    return 1.96


@dataclass
class UncertaintyState:
    id: str = field(default_factory=lambda: f"UNCERT-{uuid.uuid4().hex[:8]}")
    alpha: float = 1.0
    beta: float = 1.0
    trials: int = 0
    successes: int = 0
    failures: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UncertaintyEstimator:
    """Beta(alpha, beta) success-rate estimator with Wilson intervals."""

    def __init__(self, alpha: float = 1.0, beta: float = 1.0):
        if alpha <= 0 or beta <= 0:
            raise ValueError("alpha and beta must be > 0")
        self.state = UncertaintyState(alpha=float(alpha), beta=float(beta))

    @property
    def alpha(self) -> float:
        return self.state.alpha

    @property
    def beta(self) -> float:
        return self.state.beta

    def update(self, success: bool, weight: float = 1.0) -> None:
        weight = max(0.0, float(weight))
        if success:
            self.state.alpha += weight
            self.state.successes += 1
        else:
            self.state.beta += weight
            self.state.failures += 1
        self.state.trials += 1
        self.state.last_updated = datetime.now(timezone.utc).isoformat()

    def mean(self) -> float:
        return self.state.alpha / (self.state.alpha + self.state.beta)

    def mode(self) -> Optional[float]:
        a, b = self.state.alpha, self.state.beta
        if a > 1 and b > 1:
            return (a - 1.0) / (a + b - 2.0)
        return None

    def variance(self) -> float:
        a, b = self.state.alpha, self.state.beta
        denom = ((a + b) ** 2) * (a + b + 1.0)
        return (a * b) / denom

    def stddev(self) -> float:
        return math.sqrt(self.variance())

    def wilson_interval(self, confidence: float = 0.95) -> tuple[float, float]:
        n = self.state.successes + self.state.failures
        if n == 0:
            # Fall back to the prior's credible interval approximation.
            mean = self.mean()
            sd = self.stddev()
            z = _z_for(confidence)
            return (max(0.0, mean - z * sd), min(1.0, mean + z * sd))
        z = _z_for(confidence)
        phat = self.state.successes / n
        denom = 1.0 + (z * z) / n
        center = phat + (z * z) / (2.0 * n)
        margin = z * math.sqrt((phat * (1.0 - phat) + (z * z) / (4.0 * n)) / n)
        lower = (center - margin) / denom
        upper = (center + margin) / denom
        return (max(0.0, lower), min(1.0, upper))

    def credible_interval(self, confidence: float = 0.95) -> tuple[float, float]:
        # Approximate via mean +/- z*sd, clamped to [0, 1]. (Avoids scipy dependency.)
        z = _z_for(confidence)
        m = self.mean()
        sd = self.stddev()
        return (max(0.0, m - z * sd), min(1.0, m + z * sd))

    @staticmethod
    def ensemble_disagreement(values: list[float]) -> float:
        """Return the population standard deviation of ensemble member predictions."""
        if not values:
            return 0.0
        if len(values) == 1:
            return 0.0
        return statistics.pstdev(values)

    def summary(self) -> dict:
        lo, hi = self.wilson_interval(0.95)
        return {
            "id": self.state.id,
            "alpha": self.state.alpha,
            "beta": self.state.beta,
            "trials": self.state.trials,
            "successes": self.state.successes,
            "failures": self.state.failures,
            "mean": round(self.mean(), 4),
            "stddev": round(self.stddev(), 4),
            "wilson_95": (round(lo, 4), round(hi, 4)),
            "last_updated": self.state.last_updated,
        }


@dataclass
class EnsembleAgreement:
    """Aggregates predictions from multiple sources and reports disagreement."""

    members: dict[str, float] = field(default_factory=dict)

    def add(self, member: str, value: float) -> None:
        self.members[member] = float(value)

    def remove(self, member: str) -> bool:
        return self.members.pop(member, None) is not None

    def values(self) -> list[float]:
        return list(self.members.values())

    def disagreement(self) -> float:
        return UncertaintyEstimator.ensemble_disagreement(self.values())

    def mean(self) -> float:
        vals = self.values()
        return sum(vals) / len(vals) if vals else 0.0

    def range(self) -> tuple[float, float]:
        vals = self.values()
        if not vals:
            return (0.0, 0.0)
        return (min(vals), max(vals))

    def consensus(self, tolerance: float = 0.1) -> bool:
        lo, hi = self.range()
        return (hi - lo) <= tolerance

    def report(self) -> dict:
        return {
            "members": dict(self.members),
            "mean": round(self.mean(), 4),
            "disagreement": round(self.disagreement(), 4),
            "range": self.range(),
            "consensus_within_0.1": self.consensus(0.1),
        }
