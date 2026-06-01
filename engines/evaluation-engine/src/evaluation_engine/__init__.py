"""Evaluation Engine — Measure system performance and quality"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
import uuid


@dataclass
class EvalMetric:
    name: str
    value: float
    unit: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class EvalRun:
    id: str = field(default_factory=lambda: f"EVAL-{uuid.uuid4().hex[:8]}")
    name: str = ""
    metrics: list[EvalMetric] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EvaluationEngine:
    """Track and compare evaluation metrics."""

    def __init__(self):
        self.runs: list[EvalRun] = []
        self.baselines: dict[str, float] = {}

    def record_run(self, name: str, metrics: dict[str, float], metadata: dict = None) -> EvalRun:
        eval_run = EvalRun(name=name, metadata=metadata or {})
        for metric_name, value in metrics.items():
            eval_run.metrics.append(EvalMetric(name=metric_name, value=value))
        self.runs.append(eval_run)
        return eval_run

    def set_baseline(self, metric_name: str, value: float):
        self.baselines[metric_name] = value

    def compare_to_baseline(self, metric_name: str, current_value: float) -> dict:
        baseline = self.baselines.get(metric_name)
        if baseline is None:
            return {"metric": metric_name, "current": current_value, "baseline": None, "delta": None}
        delta = current_value - baseline
        pct_change = (delta / baseline * 100) if baseline != 0 else 0
        return {"metric": metric_name, "current": current_value, "baseline": baseline, "delta": delta, "pct_change": f"{pct_change:.1f}%"}

    def get_trend(self, metric_name: str, last_n: int = 10) -> list[dict]:
        values = []
        for run in self.runs[-last_n:]:
            for m in run.metrics:
                if m.name == metric_name:
                    values.append({"value": m.value, "timestamp": m.timestamp})
        return values
