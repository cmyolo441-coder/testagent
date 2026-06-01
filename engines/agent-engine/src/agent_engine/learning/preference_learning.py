"""Preference Learning — Online perceptron over pairwise feedback."""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
import uuid


@dataclass
class PairwisePreference:
    id: str = field(default_factory=lambda: f"PP-{uuid.uuid4().hex[:8]}")
    preferred_features: dict = field(default_factory=dict)
    rejected_features: dict = field(default_factory=dict)
    user_id: Optional[str] = None
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PreferenceLearner:
    """Learn user preferences from pairwise feedback using a simple perceptron rule."""

    def __init__(self, learning_rate: float = 0.1):
        self.weights: dict[str, float] = {}
        self.learning_rate = float(learning_rate)
        self.updates: int = 0
        self.history: list[PairwisePreference] = []

    def _score(self, features: dict) -> float:
        return sum(self.weights.get(k, 0.0) * float(v) for k, v in features.items())

    def predict(self, features: dict) -> float:
        """Predict preference score for a candidate's features."""
        return self._score(features)

    def update(
        self,
        preferred: dict,
        rejected: dict,
        user_id: Optional[str] = None,
    ) -> PairwisePreference:
        """Apply perceptron update: only correct when prediction is wrong."""
        pref_score = self._score(preferred)
        rej_score = self._score(rejected)

        if pref_score <= rej_score:
            keys = set(preferred.keys()) | set(rejected.keys())
            for k in keys:
                p = float(preferred.get(k, 0.0))
                r = float(rejected.get(k, 0.0))
                delta = self.learning_rate * (p - r)
                self.weights[k] = self.weights.get(k, 0.0) + delta
            self.updates += 1

        record = PairwisePreference(
            preferred_features=dict(preferred),
            rejected_features=dict(rejected),
            user_id=user_id,
        )
        self.history.append(record)
        return record

    def fit(self, pairs: list[tuple[dict, dict]], epochs: int = 1) -> int:
        """Run multiple update passes over a list of (preferred, rejected) pairs."""
        count = 0
        for _ in range(max(1, int(epochs))):
            for preferred, rejected in pairs:
                self.update(preferred, rejected)
                count += 1
        return count

    def rank(self, candidates: list[dict]) -> list[tuple[int, float]]:
        """Return (index, score) sorted by predicted score descending."""
        scored = [(i, self.predict(c)) for i, c in enumerate(candidates)]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def to_dict(self) -> dict:
        return {
            "weights": dict(self.weights),
            "learning_rate": self.learning_rate,
            "updates": self.updates,
            "samples": len(self.history),
        }
