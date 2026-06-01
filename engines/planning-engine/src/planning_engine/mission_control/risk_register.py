"""Risk Register — Track and manage mission risks"""
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from typing import Optional
import uuid


class RiskStatus(Enum):
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    CLOSED = "closed"
    OCCURRED = "occurred"


class RiskImpact(Enum):
    NEGLIGIBLE = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


@dataclass
class Risk:
    id: str = field(default_factory=lambda: f"RISK-{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    probability: float = 0.0  # 0-1
    impact: RiskImpact = RiskImpact.LOW
    status: RiskStatus = RiskStatus.IDENTIFIED
    mitigation: str = ""
    owner: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags: list[str] = field(default_factory=list)

    @property
    def risk_score(self) -> float:
        return self.probability * self.impact.value * 20

    @property
    def risk_level(self) -> str:
        score = self.risk_score
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        elif score >= 20:
            return "low"
        return "negligible"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "probability": self.probability,
            "impact": self.impact.name,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "status": self.status.value,
            "mitigation": self.mitigation,
            "owner": self.owner,
            "created_at": self.created_at,
            "tags": self.tags,
        }


class RiskRegister:
    """Manage risk register for a mission."""

    def __init__(self, mission_id: str):
        self.mission_id = mission_id
        self.risks: dict[str, Risk] = {}

    def add_risk(self, title: str, description: str = "", probability: float = 0.5,
                 impact: RiskImpact = RiskImpact.LOW, mitigation: str = "", tags: list[str] = None) -> Risk:
        risk = Risk(
            title=title,
            description=description,
            probability=min(max(probability, 0), 1),
            impact=impact,
            mitigation=mitigation,
            tags=tags or [],
        )
        self.risks[risk.id] = risk
        return risk

    def update_risk(self, risk_id: str, **kwargs) -> Optional[Risk]:
        risk = self.risks.get(risk_id)
        if not risk:
            return None
        for key, value in kwargs.items():
            if hasattr(risk, key):
                setattr(risk, key, value)
        return risk

    def get_risks_by_level(self, level: str) -> list[Risk]:
        return [r for r in self.risks.values() if r.risk_level == level]

    def get_top_risks(self, n: int = 5) -> list[Risk]:
        return sorted(self.risks.values(), key=lambda r: r.risk_score, reverse=True)[:n]

    def get_summary(self) -> dict:
        risks = list(self.risks.values())
        return {
            "total_risks": len(risks),
            "critical": len([r for r in risks if r.risk_level == "critical"]),
            "high": len([r for r in risks if r.risk_level == "high"]),
            "medium": len([r for r in risks if r.risk_level == "medium"]),
            "low": len([r for r in risks if r.risk_level == "low"]),
            "avg_risk_score": sum(r.risk_score for r in risks) / len(risks) if risks else 0,
            "unmitigated": len([r for r in risks if not r.mitigation and r.risk_level in ("high", "critical")]),
        }

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "risks": {k: v.to_dict() for k, v in self.risks.items()},
            "summary": self.get_summary(),
        }
