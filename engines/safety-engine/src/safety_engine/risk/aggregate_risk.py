"""Aggregate Risk — Combine multiple risk assessments into a single score"""
from dataclasses import dataclass, field
from safety_engine.risk.risk_model import RiskLevel


@dataclass
class RiskInput:
    name: str
    score: int
    weight: float = 1.0
    reasons: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class AggregatedRiskResult:
    total_score: int
    level: RiskLevel
    component_scores: dict[str, int]
    all_reasons: list[str]
    blocked: bool
    requires_approval: bool
    top_risk_factors: list[str]
    recommendation: str

    def to_dict(self) -> dict:
        return {
            "total_score": self.total_score,
            "level": self.level.name,
            "component_scores": self.component_scores,
            "all_reasons": self.all_reasons,
            "blocked": self.blocked,
            "requires_approval": self.requires_approval,
            "top_risk_factors": self.top_risk_factors,
            "recommendation": self.recommendation,
        }


class AggregateRisk:
    """Combine multiple risk assessments into a unified score."""

    AGGREGATION_STRATEGIES = {
        "max": "Take the highest individual score",
        "weighted_average": "Weighted average of all scores",
        "additive": "Sum with diminishing returns",
        "multiplicative": "Multiply normalized scores",
    }

    BLOCK_THRESHOLD = 85
    APPROVAL_THRESHOLD = 60
    SANDBOX_THRESHOLD = 40

    def __init__(self, strategy: str = "weighted_average"):
        if strategy not in self.AGGREGATION_STRATEGIES:
            raise ValueError(f"Unknown strategy: {strategy}. Use: {list(self.AGGREGATION_STRATEGIES.keys())}")
        self.strategy = strategy
        self.max_score = 100

    def aggregate(self, risks: list[RiskInput]) -> AggregatedRiskResult:
        if not risks:
            return AggregatedRiskResult(
                total_score=0,
                level=RiskLevel.SAFE,
                component_scores={},
                all_reasons=[],
                blocked=False,
                requires_approval=False,
                top_risk_factors=[],
                recommendation="No risks assessed",
            )

        component_scores = {r.name: r.score for r in risks}
        all_reasons = []
        for r in risks:
            all_reasons.extend(f"{r.name}: {reason}" for reason in r.reasons)

        if self.strategy == "max":
            total_score = max(r.score for r in risks)
        elif self.strategy == "weighted_average":
            total_weight = sum(r.weight for r in risks)
            if total_weight == 0:
                total_score = 0
            else:
                total_score = sum(r.score * r.weight for r in risks) / total_weight
        elif self.strategy == "additive":
            raw_sum = sum(r.score * r.weight for r in risks)
            import math
            total_score = self.max_score * (1 - math.exp(-raw_sum / self.max_score))
        elif self.strategy == "multiplicative":
            normalized = [r.score / self.max_score for r in risks if r.score > 0]
            if normalized:
                product = 1.0
                for n in normalized:
                    product *= (1 - n)
                total_score = self.max_score * (1 - product)
            else:
                total_score = 0
        else:
            total_score = 0

        total_score = min(self.max_score, max(0, int(total_score)))

        sorted_risks = sorted(risks, key=lambda r: r.score * r.weight, reverse=True)
        top_risk_factors = [f"{r.name} ({r.score})" for r in sorted_risks[:3] if r.score > 0]

        blocked = any(r.score >= self.BLOCK_THRESHOLD for r in risks) or total_score >= self.BLOCK_THRESHOLD
        requires_approval = any(r.score >= self.APPROVAL_THRESHOLD for r in risks) or total_score >= self.APPROVAL_THRESHOLD

        level = self._score_to_level(total_score)

        recommendation = self._build_recommendation(total_score, level, blocked, requires_approval, risks)

        return AggregatedRiskResult(
            total_score=total_score,
            level=level,
            component_scores=component_scores,
            all_reasons=all_reasons,
            blocked=blocked,
            requires_approval=requires_approval,
            top_risk_factors=top_risk_factors,
            recommendation=recommendation,
        )

    def _build_recommendation(self, total_score: int, level: RiskLevel,
                               blocked: bool, requires_approval: bool,
                               risks: list[RiskInput]) -> str:
        if blocked:
            blocked_names = [r.name for r in risks if r.score >= self.BLOCK_THRESHOLD]
            return f"BLOCKED: Critical risk in {', '.join(blocked_names)}. Manual review required."

        if level == RiskLevel.HIGH:
            return "High risk operation. Requires explicit approval before execution."

        if level == RiskLevel.MEDIUM:
            return "Medium risk. Approval recommended. Consider running in sandbox."

        if level == RiskLevel.LOW:
            return "Low risk. Auto-approval may apply. Monitor for anomalies."

        return "Safe operation. No approval required."

    def _score_to_level(self, score: int) -> RiskLevel:
        if score >= 80:
            return RiskLevel.CRITICAL
        if score >= 60:
            return RiskLevel.HIGH
        if score >= 40:
            return RiskLevel.MEDIUM
        if score >= 20:
            return RiskLevel.LOW
        return RiskLevel.SAFE
