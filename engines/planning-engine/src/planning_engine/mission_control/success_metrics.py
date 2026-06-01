"""Success Metrics — Define and track mission success criteria"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SuccessMetric:
    name: str
    target: float
    current: float = 0.0
    unit: str = ""
    weight: float = 1.0

    @property
    def achievement(self) -> float:
        return self.current / self.target if self.target > 0 else 0

    @property
    def is_met(self) -> bool:
        return self.current >= self.target


class SuccessMetrics:
    """Track mission success metrics."""

    def __init__(self):
        self.metrics: dict[str, SuccessMetric] = {}

    def add_metric(self, name: str, target: float, unit: str = "", weight: float = 1.0):
        self.metrics[name] = SuccessMetric(name=name, target=target, unit=unit, weight=weight)

    def update(self, name: str, current: float):
        metric = self.metrics.get(name)
        if metric:
            metric.current = current

    def get_overall_score(self) -> float:
        if not self.metrics:
            return 0
        weighted_sum = sum(m.achievement * m.weight for m in self.metrics.values())
        total_weight = sum(m.weight for m in self.metrics.values())
        return weighted_sum / total_weight if total_weight > 0 else 0

    def get_summary(self) -> dict:
        return {
            "metrics": {name: {"target": m.target, "current": m.current, "achievement": f"{m.achievement:.0%}"}
                       for name, m in self.metrics.items()},
            "overall_score": f"{self.get_overall_score():.0%}",
            "met": sum(1 for m in self.metrics.values() if m.is_met),
            "total": len(self.metrics),
        }
