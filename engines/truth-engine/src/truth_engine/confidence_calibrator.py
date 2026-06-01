"""Confidence Calibrator — adjusts raw model confidences using Platt-like scaling
and observed accuracy history.
"""
from dataclasses import dataclass, field
from typing import Optional
import math


@dataclass
class CalibrationSample:
    raw_confidence: float
    correct: bool


@dataclass
class ConfidenceCalibrator:
    """Maintains a sliding window of (predicted_confidence, was_correct) and
    fits a simple sigmoid calibration each update.
    """
    window: int = 500
    a: float = 1.0          # slope
    b: float = 0.0          # bias
    samples: list = field(default_factory=list)

    def record(self, raw: float, correct: bool) -> None:
        self.samples.append(CalibrationSample(raw, correct))
        if len(self.samples) > self.window:
            self.samples = self.samples[-self.window:]
        if len(self.samples) >= 25:
            self._fit()

    def _fit(self) -> None:
        # closed-form-ish: scale so observed empirical accuracy matches sigmoid(a*x+b)
        # use simple grid search on (a,b) — robust, no scipy dep
        best = (1.0, 0.0, 1e9)
        for a in [0.5, 1.0, 1.5, 2.0, 3.0]:
            for b in [-2.0, -1.0, 0.0, 1.0, 2.0]:
                loss = sum(
                    (self._sig(a * s.raw_confidence + b) - (1.0 if s.correct else 0.0)) ** 2
                    for s in self.samples
                )
                if loss < best[2]:
                    best = (a, b, loss)
        self.a, self.b, _ = best

    @staticmethod
    def _sig(x: float) -> float:
        if x > 50:  return 1.0
        if x < -50: return 0.0
        return 1.0 / (1.0 + math.exp(-x))

    def calibrate(self, raw: float) -> float:
        """Apply learned calibration to a fresh raw confidence."""
        return self._sig(self.a * raw + self.b)

    def expected_calibration_error(self, bins: int = 10) -> float:
        if not self.samples: return 0.0
        bucketed: list[list[CalibrationSample]] = [[] for _ in range(bins)]
        for s in self.samples:
            idx = min(bins - 1, int(s.raw_confidence * bins))
            bucketed[idx].append(s)
        ece = 0.0
        n = len(self.samples)
        for b, bucket in enumerate(bucketed):
            if not bucket: continue
            avg_conf = sum(s.raw_confidence for s in bucket) / len(bucket)
            accuracy = sum(1 for s in bucket if s.correct) / len(bucket)
            ece += (len(bucket) / n) * abs(avg_conf - accuracy)
        return ece

    def report(self) -> dict:
        return {
            "samples": len(self.samples),
            "a": self.a, "b": self.b,
            "ece": self.expected_calibration_error(),
        }
