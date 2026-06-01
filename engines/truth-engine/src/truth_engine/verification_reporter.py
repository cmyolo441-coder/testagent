"""Verification Reporter — Generate verification reports with levels"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from enum import Enum
import uuid


class VerificationLevel(Enum):
    UNVERIFIED = 0
    INTERNALLY_CONSISTENT = 1
    SOURCE_SUPPORTED = 2
    INDEPENDENTLY_REPRODUCED = 3
    ADVERSARIAL_REVIEWED = 4
    FORMALLY_PROVEN = 5


class VerificationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    REFUTED = "refuted"
    PARTIALLY_VERIFIED = "partially_verified"


@dataclass
class Evidence:
    id: str = field(default_factory=lambda: f"EVD-{uuid.uuid4().hex[:8]}")
    type: str = ""  # source, experiment, proof, observation, testimonial
    description: str = ""
    source: str = ""
    reliability: float = 0.5  # 0-1
    url: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class VerificationReport:
    id: str = field(default_factory=lambda: f"VR-{uuid.uuid4().hex[:8]}")
    claim_id: str = ""
    claim_text: str = ""
    verification_level: VerificationLevel = VerificationLevel.UNVERIFIED
    status: VerificationStatus = VerificationStatus.PENDING
    confidence: float = 0.0  # 0-1
    evidence: list[Evidence] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    assessor: str = "system"  # system, agent, human, adversarial
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def evidence_count(self) -> int:
        return len(self.evidence)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "verification_level": self.verification_level.value,
            "status": self.status.value,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "contradictions": self.contradictions,
            "assessor": self.assessor,
            "notes": self.notes,
            "created_at": self.created_at,
        }


class VerificationReporter:
    """Generate and manage verification reports."""

    def __init__(self):
        self.reports: dict[str, VerificationReport] = {}

    def create_report(self, claim_id: str, claim_text: str,
                     assessor: str = "system") -> VerificationReport:
        report = VerificationReport(
            claim_id=claim_id,
            claim_text=claim_text,
            assessor=assessor,
        )
        self.reports[report.id] = report
        return report

    def add_evidence(self, report_id: str, evidence_type: str, description: str,
                    source: str, reliability: float = 0.5) -> Optional[Evidence]:
        report = self.reports.get(report_id)
        if not report:
            return None

        evidence = Evidence(
            type=evidence_type,
            description=description,
            source=source,
            reliability=reliability,
        )
        report.evidence.append(evidence)
        report.updated_at = datetime.now(timezone.utc).isoformat()

        # Auto-update verification level based on evidence
        self._update_level(report)
        return evidence

    def add_contradiction(self, report_id: str, description: str) -> bool:
        report = self.reports.get(report_id)
        if not report:
            return False
        report.contradictions.append(description)
        report.status = VerificationStatus.DISPUTED
        report.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def finalize(self, report_id: str, status: VerificationStatus,
                confidence: float, notes: str = "") -> Optional[VerificationReport]:
        report = self.reports.get(report_id)
        if not report:
            return None
        report.status = status
        report.confidence = confidence
        report.notes = notes
        report.updated_at = datetime.now(timezone.utc).isoformat()
        self._update_level(report)
        return report

    def get_report(self, report_id: str) -> Optional[VerificationReport]:
        return self.reports.get(report_id)

    def get_by_claim(self, claim_id: str) -> Optional[VerificationReport]:
        for report in self.reports.values():
            if report.claim_id == claim_id:
                return report
        return None

    def get_pending(self) -> list[VerificationReport]:
        return [r for r in self.reports.values() if r.status == VerificationStatus.PENDING]

    def _update_level(self, report: VerificationReport):
        evidence_count = len(report.evidence)
        avg_reliability = (
            sum(e.reliability for e in report.evidence) / evidence_count
            if evidence_count > 0 else 0
        )
        contradiction_count = len(report.contradictions)

        if contradiction_count > 0:
            report.verification_level = VerificationLevel.UNVERIFIED
            report.confidence = max(0, report.confidence - 0.2)
        elif evidence_count == 0:
            report.verification_level = VerificationLevel.UNVERIFIED
        elif evidence_count == 1 and avg_reliability > 0.7:
            report.verification_level = VerificationLevel.SOURCE_SUPPORTED
        elif evidence_count >= 2 and avg_reliability > 0.8:
            report.verification_level = VerificationLevel.INDEPENDENTLY_REPRODUCED
        elif evidence_count >= 3 and avg_reliability > 0.9 and contradiction_count == 0:
            report.verification_level = VerificationLevel.ADVERSARIAL_REVIEWED
        else:
            report.verification_level = VerificationLevel.INTERNALLY_CONSISTENT

        report.confidence = min(1.0, avg_reliability * (evidence_count / max(evidence_count, 3)))

    def generate_report(self, claims: list, target_level: int = 2) -> dict:
        """Build a one-shot verification report over a batch of claims."""
        report = {
            "claim_count": len(claims),
            "target_level": target_level,
            "claims": [],
            "summary": {"verified": 0, "unverified": 0, "disputed": 0},
        }
        for c in claims:
            r = self.create_report(getattr(c, "id", str(id(c))), getattr(c, "text", str(c)))
            # Heuristic: high-confidence non-negated claims get level-1+, statistical claims need source
            conf_name = getattr(getattr(c, "confidence", None), "value", "medium")
            if not getattr(c, "negated", False) and conf_name == "high":
                r.verification_level = VerificationLevel.INTERNALLY_CONSISTENT
                r.status = VerificationStatus.PARTIALLY_VERIFIED
                report["summary"]["verified"] += 1
            else:
                r.status = VerificationStatus.PENDING
                report["summary"]["unverified"] += 1
            report["claims"].append(r.to_dict())
        return report

    def get_summary(self) -> dict:
        reports = list(self.reports.values())
        by_level = {}
        for r in reports:
            level_name = r.verification_level.name
            by_level[level_name] = by_level.get(level_name, 0) + 1
        return {
            "total_reports": len(reports),
            "by_level": by_level,
            "pending": len([r for r in reports if r.status == VerificationStatus.PENDING]),
            "verified": len([r for r in reports if r.status == VerificationStatus.VERIFIED]),
            "disputed": len([r for r in reports if r.status == VerificationStatus.DISPUTED]),
        }
