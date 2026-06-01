"""Verification Evidence Widget — Evidence display and management"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class EvidenceItem:
    id: str = ""
    claim_id: str = ""
    evidence_type: str = ""  # observation, measurement, testimony, document, inference
    content: str = ""
    is_supporting: bool = True
    confidence: float = 0.7
    source: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict = field(default_factory=dict)


class VerificationEvidence:
    """Evidence display and management widget."""

    def __init__(self, claim_id: str = ""):
        self.claim_id = claim_id
        self.evidence: list[EvidenceItem] = []

    def add_evidence(self, content: str, evidence_type: str = "observation",
                     is_supporting: bool = True, confidence: float = 0.7,
                     source: str = "", metadata: dict = None) -> EvidenceItem:
        item = EvidenceItem(
            id=f"EVD-{len(self.evidence) + 1:04d}",
            claim_id=self.claim_id,
            evidence_type=evidence_type,
            content=content,
            is_supporting=is_supporting,
            confidence=confidence,
            source=source,
            metadata=metadata or {},
        )
        self.evidence.append(item)
        return item

    def remove_evidence(self, evidence_id: str) -> bool:
        for i, item in enumerate(self.evidence):
            if item.id == evidence_id:
                self.evidence.pop(i)
                return True
        return False

    def get_supporting(self) -> list[EvidenceItem]:
        return [e for e in self.evidence if e.is_supporting]

    def get_counter(self) -> list[EvidenceItem]:
        return [e for e in self.evidence if not e.is_supporting]

    def get_by_type(self, evidence_type: str) -> list[EvidenceItem]:
        return [e for e in self.evidence if e.evidence_type == evidence_type]

    def get_balance_score(self) -> float:
        supporting = sum(e.confidence for e in self.get_supporting())
        counter = sum(e.confidence for e in self.get_counter())
        total = supporting + counter
        if total == 0:
            return 0.5
        return supporting / total

    def get_overall_confidence(self) -> float:
        if not self.evidence:
            return 0.0
        return sum(e.confidence for e in self.evidence) / len(self.evidence)

    def render_supporting(self) -> str:
        lines = ["┌─ Supporting Evidence ───────────────────────────────┐"]
        for item in self.get_supporting()[:5]:
            conf = f"{item.confidence:.0%}"
            lines.append(f"│ + [{item.evidence_type[:6]}] {item.content[:30]:<30} {conf:>5} │")
        if not self.get_supporting():
            lines.append(f"│ {'No supporting evidence':<52} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_counter(self) -> str:
        lines = ["┌─ Counter Evidence ──────────────────────────────────┐"]
        for item in self.get_counter()[:5]:
            conf = f"{item.confidence:.0%}"
            lines.append(f"│ - [{item.evidence_type[:6]}] {item.content[:30]:<30} {conf:>5} │")
        if not self.get_counter():
            lines.append(f"│ {'No counter evidence':<52} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_balance(self) -> str:
        balance = self.get_balance_score()
        bar_width = 20
        supporting_width = int(balance * bar_width)
        counter_width = bar_width - supporting_width
        bar = "+" * supporting_width + "-" * counter_width
        return f"Balance: [{bar}] {balance:.0%} supporting"

    def render(self) -> str:
        parts = [
            self.render_supporting(),
            "",
            self.render_counter(),
            "",
            self.render_balance(),
        ]
        return "\n".join(parts)

    def get_stats(self) -> dict:
        return {
            "total_evidence": len(self.evidence),
            "supporting": len(self.get_supporting()),
            "counter": len(self.get_counter()),
            "balance_score": self.get_balance_score(),
            "overall_confidence": self.get_overall_confidence(),
        }
