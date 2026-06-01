"""Science Lab Screen — Hypothesis and experiment management"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Hypothesis:
    id: str = ""
    statement: str = ""
    description: str = ""
    status: str = "proposed"  # proposed, testing, confirmed, refuted, revised
    confidence: float = 0.5
    experiments: list[str] = field(default_factory=list)
    evidence_for: list[str] = field(default_factory=list)
    evidence_against: list[str] = field(default_factory=list)
    domain: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Experiment:
    id: str = ""
    hypothesis_id: str = ""
    name: str = ""
    description: str = ""
    method: str = ""
    status: str = "planned"  # planned, running, completed, failed
    result: Optional[str] = None
    data: dict = field(default_factory=dict)
    conclusion: str = ""
    duration_seconds: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


class ScienceLabScreen:
    """Hypothesis and experiment management screen."""

    TITLE = "Science Lab"

    def __init__(self):
        self.hypotheses: dict[str, Hypothesis] = {}
        self.experiments: dict[str, Experiment] = {}
        self.selected_hypothesis_id: Optional[str] = None

    def propose_hypothesis(self, statement: str, description: str = "",
                           domain: str = "general", confidence: float = 0.5,
                           tags: list[str] = None) -> Hypothesis:
        hyp_id = f"HYP-{len(self.hypotheses) + 1:04d}"
        hypothesis = Hypothesis(
            id=hyp_id,
            statement=statement,
            description=description,
            domain=domain,
            confidence=confidence,
            tags=tags or [],
        )
        self.hypotheses[hyp_id] = hypothesis
        return hypothesis

    def design_experiment(self, hypothesis_id: str, name: str,
                          description: str = "", method: str = "") -> Optional[Experiment]:
        if hypothesis_id not in self.hypotheses:
            return None
        exp_id = f"EXP-{len(self.experiments) + 1:04d}"
        experiment = Experiment(
            id=exp_id,
            hypothesis_id=hypothesis_id,
            name=name,
            description=description,
            method=method,
        )
        self.experiments[exp_id] = experiment
        self.hypotheses[hypothesis_id].experiments.append(exp_id)
        return experiment

    def run_experiment(self, experiment_id: str) -> Optional[Experiment]:
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None
        experiment.status = "running"
        return experiment

    def complete_experiment(self, experiment_id: str, result: str,
                            conclusion: str = "", data: dict = None) -> Optional[Experiment]:
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None
        experiment.status = "completed"
        experiment.result = result
        experiment.conclusion = conclusion
        experiment.data = data or {}
        experiment.completed_at = datetime.now(timezone.utc).isoformat()
        self._update_hypothesis_from_experiment(experiment)
        return experiment

    def _update_hypothesis_from_experiment(self, experiment: Experiment):
        hypothesis = self.hypotheses.get(experiment.hypothesis_id)
        if not hypothesis:
            return
        if experiment.result == "supported":
            hypothesis.evidence_for.append(experiment.conclusion)
            hypothesis.confidence = min(1.0, hypothesis.confidence + 0.1)
        elif experiment.result == "contradicted":
            hypothesis.evidence_against.append(experiment.conclusion)
            hypothesis.confidence = max(0.0, hypothesis.confidence - 0.15)
        hypothesis.updated_at = datetime.now(timezone.utc).isoformat()

    def get_confirmed_hypotheses(self) -> list[Hypothesis]:
        return [h for h in self.hypotheses.values() if h.status == "confirmed"]

    def get_refuted_hypotheses(self) -> list[Hypothesis]:
        return [h for h in self.hypotheses.values() if h.status == "refuted"]

    def get_active_experiments(self) -> list[Experiment]:
        return [e for e in self.experiments.values() if e.status in ("planned", "running")]

    def get_domain_stats(self) -> dict[str, dict]:
        domains = {}
        for h in self.hypotheses.values():
            if h.domain not in domains:
                domains[h.domain] = {"count": 0, "avg_confidence": 0.0}
            domains[h.domain]["count"] += 1
        for domain, stats in domains.items():
            hyps = [h for h in self.hypotheses.values() if h.domain == domain]
            stats["avg_confidence"] = sum(h.confidence for h in hyps) / len(hyps) if hyps else 0
        return domains

    def render_header(self) -> str:
        hyp_count = len(self.hypotheses)
        exp_count = len(self.experiments)
        confirmed = len(self.get_confirmed_hypotheses())
        return f"╔══════════════════════════════════════════════════════════╗\n║ SCIENCE LAB — {hyp_count} hypotheses, {exp_count} experiments{'':<12}║\n║ Confirmed: {confirmed}, Active experiments: {len(self.get_active_experiments())}{'':<18}║\n╚══════════════════════════════════════════════════════════╝"

    def render_hypotheses(self) -> str:
        lines = ["┌─ Hypotheses ───────────────────────────────────────┐"]
        status_icons = {"proposed": "○", "testing": "◐", "confirmed": "●", "refuted": "✗"}
        for h in list(self.hypotheses.values())[:6]:
            icon = status_icons.get(h.status, "?")
            conf = f"{h.confidence:.0%}"
            lines.append(f"│ {icon} {h.statement[:35]:<35} {conf:>5} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_experiments(self) -> str:
        lines = ["┌─ Experiments ───────────────────────────────────────┐"]
        for e in list(self.experiments.values())[:5]:
            status_icon = {"planned": "○", "running": "●", "completed": "✓", "failed": "✗"}.get(e.status, "?")
            lines.append(f"│ {status_icon} {e.name[:30]:<30} {e.status:<10} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_full(self) -> str:
        parts = [
            self.render_header(),
            "",
            self.render_hypotheses(),
            "",
            self.render_experiments(),
        ]
        return "\n".join(parts)

    def get_stats(self) -> dict:
        return {
            "total_hypotheses": len(self.hypotheses),
            "total_experiments": len(self.experiments),
            "confirmed": len(self.get_confirmed_hypotheses()),
            "refuted": len(self.get_refuted_hypotheses()),
            "active_experiments": len(self.get_active_experiments()),
        }
