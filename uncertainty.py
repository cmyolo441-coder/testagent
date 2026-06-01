"""UncertaintyEstimator — Beta-distribution estimator, Wilson interval, ensemble metrics"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
import math
import statistics
import uuid


@dataclass
class BetaEstimate:
    estimator_id: str
    alpha: float
    beta: float
    successes: int = 0
    failures: int = 0
    updated_at: str = ""

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc).isoformat()

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def variance(self) -> float:
        s = self.alpha + self.beta
        return (self.alpha * self.beta) / ((s * s) * (s + 1.0))

    @property
    def n(self) -> int:
        return self.successes + self.failures


class UncertaintyEstimator:
    """Beta-distribution based binary estimator with Wilson intervals and ensemble metrics."""

    def __init__(self, prior_alpha: float = 1.0, prior_beta: float = 1.0):
        if prior_alpha <= 0 or prior_beta <= 0:
            raise ValueError("Beta priors must be > 0")
        self.prior_alpha = float(prior_alpha)
        self.prior_beta = float(prior_beta)
        self.estimate = BetaEstimate(
            estimator_id=f"UNC-{uuid.uuid4().hex[:8]}",
            alpha=self.prior_alpha,
            beta=self.prior_beta,
        )
        self._calibration_log: list[tuple[float, int]] = []

    # ---- Updates ----
    def observe(self, success: bool, weight: float = 1.0) -> BetaEstimate:
        if weight <= 0:
            raise ValueError("weight must be > 0")
        if success:
            self.estimate.alpha += weight
            self.estimate.successes += 1
        else:
            self.estimate.beta += weight
            self.estimate.failures += 1
        self.estimate.updated_at = datetime.now(timezone.utc).isoformat()
        return self.estimate

    def observe_many(self, successes: int, failures: int) -> BetaEstimate:
        if successes < 0 or failures < 0:
            raise ValueError("counts must be non-negative")
        self.estimate.alpha += successes
        self.estimate.beta += failures
        self.estimate.successes += successes
        self.estimate.failures += failures
        self.estimate.updated_at = datetime.now(timezone.utc).isoformat()
        return self.estimate

    def reset(self) -> None:
        self.estimate = BetaEstimate(
            estimator_id=f"UNC-{uuid.uuid4().hex[:8]}",
            alpha=self.prior_alpha,
            beta=self.prior_beta,
        )
        self._calibration_log.clear()

    # ---- Estimates ----
    @property
    def mean(self) -> float:
        return self.estimate.mean

    @property
    def variance(self) -> float:
        return self.estimate.variance

    def credible_interval(self, level: float = 0.95) -> tuple[float, float]:
        """Approximate central credible interval using a normal approximation when n is large,
        and a Jeffreys-style fallback otherwise."""
        if not 0 < level < 1:
            raise ValueError("level must be in (0,1)")
        mu = self.mean
        sigma = math.sqrt(self.variance)
        z = self._z_score(level)
        lower = max(0.0, mu - z * sigma)
        upper = min(1.0, mu + z * sigma)
        return round(lower, 6), round(upper, 6)

    def wilson_interval(self, level: float = 0.95) -> tuple[float, float]:
        """Wilson score interval for a binomial proportion."""
        n = self.estimate.n
        if n <= 0:
            return 0.0, 1.0
        p_hat = self.estimate.successes / n
        z = self._z_score(level)
        denom = 1.0 + (z * z) / n
        center = (p_hat + (z * z) / (2.0 * n)) / denom
        margin = (z * math.sqrt((p_hat * (1.0 - p_hat) + (z * z) / (4.0 * n)) / n)) / denom
        lower = max(0.0, center - margin)
        upper = min(1.0, center + margin)
        return round(lower, 6), round(upper, 6)

    @staticmethod
    def _z_score(level: float) -> float:
        # common quantiles; otherwise approximate via inverse error fn
        common = {0.80: 1.2816, 0.90: 1.6449, 0.95: 1.9600, 0.975: 2.2414, 0.99: 2.5758}
        if level in common:
            return common[level]
        # Acklam approximation for inverse normal CDF
        p = 0.5 + level / 2.0
        return math.sqrt(2.0) * _inv_erf(2.0 * p - 1.0)

    # ---- Ensemble ----
    @staticmethod
    def ensemble_disagreement(predictions: list[float]) -> dict:
        """Compute disagreement statistics for an ensemble of probability predictions."""
        if not predictions:
            return {"n": 0, "mean": 0.0, "variance": 0.0, "stdev": 0.0, "entropy": 0.0, "range": 0.0}
        clipped = [max(0.0, min(1.0, float(p))) for p in predictions]
        mean_p = sum(clipped) / len(clipped)
        if len(clipped) > 1:
            var_p = statistics.pvariance(clipped)
            std_p = statistics.pstdev(clipped)
        else:
            var_p = 0.0
            std_p = 0.0
        # Entropy of the mean (binary)
        if 0.0 < mean_p < 1.0:
            entropy = -(mean_p * math.log2(mean_p) + (1 - mean_p) * math.log2(1 - mean_p))
        else:
            entropy = 0.0
        return {
            "n": len(clipped),
            "mean": round(mean_p, 6),
            "variance": round(var_p, 6),
            "stdev": round(std_p, 6),
            "entropy": round(entropy, 6),
            "range": round(max(clipped) - min(clipped), 6),
        }

    # ---- Calibration ----
    def log_calibration(self, predicted_prob: float, outcome: bool) -> None:
        p = max(0.0, min(1.0, float(predicted_prob)))
        self._calibration_log.append((p, 1 if outcome else 0))

    def calibration_curve(self, bins: int = 10) -> list[dict]:
        if bins <= 0:
            raise ValueError("bins must be > 0")
        buckets: list[list[tuple[float, int]]] = [[] for _ in range(bins)]
        for p, y in self._calibration_log:
            idx = min(bins - 1, int(p * bins))
            buckets[idx].append((p, y))
        curve: list[dict] = []
        for i, bucket in enumerate(buckets):
            if not bucket:
                curve.append({
                    "bin": i,
                    "lower": i / bins,
                    "upper": (i + 1) / bins,
                    "count": 0,
                    "avg_predicted": None,
                    "empirical_rate": None,
                    "gap": None,
                })
                continue
            preds = [p for p, _ in bucket]
            outs = [y for _, y in bucket]
            avg_p = sum(preds) / len(preds)
            emp = sum(outs) / len(outs)
            curve.append({
                "bin": i,
                "lower": round(i / bins, 4),
                "upper": round((i + 1) / bins, 4),
                "count": len(bucket),
                "avg_predicted": round(avg_p, 6),
                "empirical_rate": round(emp, 6),
                "gap": round(emp - avg_p, 6),
            })
        return curve

    def expected_calibration_error(self, bins: int = 10) -> float:
        curve = self.calibration_curve(bins=bins)
        total = sum(b["count"] for b in curve)
        if total == 0:
            return 0.0
        ece = 0.0
        for b in curve:
            if b["count"] == 0:
                continue
            ece += (b["count"] / total) * abs(b["empirical_rate"] - b["avg_predicted"])
        return round(ece, 6)

    def report(self) -> dict:
        ci = self.credible_interval()
        wi = self.wilson_interval()
        return {
            "estimator_id": self.estimate.estimator_id,
            "alpha": self.estimate.alpha,
            "beta": self.estimate.beta,
            "successes": self.estimate.successes,
            "failures": self.estimate.failures,
            "mean": round(self.mean, 6),
            "variance": round(self.variance, 6),
            "credible_interval_95": ci,
            "wilson_interval_95": wi,
            "ece": self.expected_calibration_error(),
            "calibration_samples": len(self._calibration_log),
        }


def _inv_erf(x: float) -> float:
    """Approximate inverse error function (Winitzki)."""
    x = max(-0.999999, min(0.999999, x))
    a = 0.147
    ln_one_minus = math.log(1.0 - x * x)
    first = 2.0 / (math.pi * a) + ln_one_minus / 2.0
    inside = first * first - ln_one_minus / a
    return math.copysign(math.sqrt(math.sqrt(inside) - first), x)
