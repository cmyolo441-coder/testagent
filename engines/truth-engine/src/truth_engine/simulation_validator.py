"""Simulation Validator — compare simulation output against expectations.

Supports tolerance-based numerical match, distributional check (mean/std),
and qualitative trend check (monotonic increase/decrease).
"""
from dataclasses import dataclass
import statistics


@dataclass
class SimValidation:
    matched: bool
    deviation: float
    method: str
    detail: str


class SimulationValidator:
    def numerical(self, expected: float, actual: float, rel_tol: float = 0.05) -> SimValidation:
        denom = abs(expected) if expected else 1.0
        dev = abs(actual - expected) / denom
        return SimValidation(matched=dev <= rel_tol, deviation=dev, method="numerical",
                             detail=f"|{actual} - {expected}| / |{expected}| = {dev:.4f}")

    def distributional(self, expected: list[float], actual: list[float],
                       tol_mean: float = 0.1, tol_std: float = 0.2) -> SimValidation:
        if not expected or not actual:
            return SimValidation(False, 1.0, "distributional", "empty inputs")
        em, am = statistics.fmean(expected), statistics.fmean(actual)
        es = statistics.pstdev(expected) or 1e-6
        as_ = statistics.pstdev(actual)
        mean_dev = abs(am - em) / max(abs(em), 1e-6)
        std_dev = abs(as_ - es) / max(es, 1e-6)
        ok = mean_dev <= tol_mean and std_dev <= tol_std
        return SimValidation(ok, max(mean_dev, std_dev), "distributional",
                             f"mean_dev={mean_dev:.3f}, std_dev={std_dev:.3f}")

    def monotonic(self, series: list[float], direction: str = "increasing") -> SimValidation:
        if len(series) < 2:
            return SimValidation(False, 1.0, "monotonic", "too few points")
        deltas = [b - a for a, b in zip(series, series[1:])]
        if direction == "increasing":
            ok = all(d >= 0 for d in deltas)
        else:
            ok = all(d <= 0 for d in deltas)
        violations = sum(1 for d in deltas if (direction == "increasing") != (d >= 0))
        return SimValidation(ok, violations / len(deltas), "monotonic",
                             f"violations={violations}/{len(deltas)}")
