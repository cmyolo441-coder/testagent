"""Truth Panel Screen — Verification status and claims display"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Claim:
    id: str = ""
    statement: str = ""
    claim_type: str = ""  # factual, prediction, assessment, recommendation
    status: str = "pending"  # pending, verified, disproven, uncertain
    confidence: float = 0.5
    evidence: list[str] = field(default_factory=list)
    counter_evidence: list[str] = field(default_factory=list)
    source: str = ""
    verified_by: Optional[str] = None
    mission_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verified_at: Optional[str] = None


@dataclass
class VerificationResult:
    claim_id: str
    verdict: str  # confirmed, refuted, inconclusive
    confidence: float
    evidence_summary: str
    verifier: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TruthPanelScreen:
    """Verification status and claims display screen."""

    TITLE = "Truth Panel"

    def __init__(self):
        self.claims: dict[str, Claim] = {}
        self.verifications: list[VerificationResult] = []
        self.selected_claim_id: Optional[str] = None

    def submit_claim(self, statement: str, claim_type: str = "factual",
                     confidence: float = 0.5, source: str = "",
                     evidence: list[str] = None, tags: list[str] = None) -> Claim:
        claim_id = f"CLM-{len(self.claims) + 1:04d}"
        claim = Claim(
            id=claim_id,
            statement=statement,
            claim_type=claim_type,
            confidence=confidence,
            source=source,
            evidence=evidence or [],
            tags=tags or [],
        )
        self.claims[claim_id] = claim
        return claim

    def verify_claim(self, claim_id: str, verdict: str, confidence: float,
                     evidence_summary: str = "", verifier: str = "") -> Optional[VerificationResult]:
        claim = self.claims.get(claim_id)
        if not claim:
            return None

        result = VerificationResult(
            claim_id=claim_id,
            verdict=verdict,
            confidence=confidence,
            evidence_summary=evidence_summary,
            verifier=verifier,
        )
        self.verifications.append(result)

        if verdict == "confirmed":
            claim.status = "verified"
            claim.confidence = min(1.0, (claim.confidence + confidence) / 2)
        elif verdict == "refuted":
            claim.status = "disproven"
        else:
            claim.status = "uncertain"

        claim.verified_by = verifier
        claim.verified_at = result.timestamp
        return result

    def add_evidence(self, claim_id: str, evidence: str, is_counter: bool = False) -> bool:
        claim = self.claims.get(claim_id)
        if not claim:
            return False
        if is_counter:
            claim.counter_evidence.append(evidence)
        else:
            claim.evidence.append(evidence)
        return True

    def get_verified_claims(self) -> list[Claim]:
        return [c for c in self.claims.values() if c.status == "verified"]

    def get_disproven_claims(self) -> list[Claim]:
        return [c for c in self.claims.values() if c.status == "disproven"]

    def get_pending_claims(self) -> list[Claim]:
        return [c for c in self.claims.values() if c.status == "pending"]

    def get_uncertain_claims(self) -> list[Claim]:
        return [c for c in self.claims.values() if c.status == "uncertain"]

    def get_claim_history(self, claim_id: str) -> list[VerificationResult]:
        return [v for v in self.verifications if v.claim_id == claim_id]

    def get_confidence_distribution(self) -> dict[str, int]:
        buckets = {"high (>0.8)": 0, "medium (0.5-0.8)": 0, "low (<0.5)": 0}
        for claim in self.claims.values():
            if claim.confidence > 0.8:
                buckets["high (>0.8)"] += 1
            elif claim.confidence >= 0.5:
                buckets["medium (0.5-0.8)"] += 1
            else:
                buckets["low (<0.5)"] += 1
        return buckets

    def render_header(self) -> str:
        total = len(self.claims)
        verified = len(self.get_verified_claims())
        disproven = len(self.get_disproven_claims())
        return f"╔══════════════════════════════════════════════════════════╗\n║ TRUTH PANEL — {total} claims ({verified} verified, {disproven} disproven){'':<8}║\n╚══════════════════════════════════════════════════════════╝"

    def render_claims_table(self) -> str:
        lines = ["┌─ Claims ──────────────────────────────────────────────┐"]
        status_icons = {"verified": "✓", "disproven": "✗", "pending": "?", "uncertain": "~"}
        for claim in list(self.claims.values())[:8]:
            icon = status_icons.get(claim.status, "?")
            conf = f"{claim.confidence:.0%}"
            lines.append(f"│ {icon} {claim.statement[:35]:<35} {conf:>5} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_verification_stats(self) -> str:
        dist = self.get_confidence_distribution()
        lines = [
            "┌─ Verification Stats ─────────────────────────────────┐",
            f"│ High confidence:   {dist.get('high (>0.8)', 0):<32} │",
            f"│ Medium confidence: {dist.get('medium (0.5-0.8)', 0):<32} │",
            f"│ Low confidence:    {dist.get('low (<0.5)', 0):<32} │",
            "└────────────────────────────────────────────────────┘",
        ]
        return "\n".join(lines)

    def render_full(self) -> str:
        parts = [
            self.render_header(),
            "",
            self.render_claims_table(),
            "",
            self.render_verification_stats(),
        ]
        return "\n".join(parts)

    def get_stats(self) -> dict:
        claims = list(self.claims.values())
        return {
            "total_claims": len(claims),
            "verified": len(self.get_verified_claims()),
            "disproven": len(self.get_disproven_claims()),
            "pending": len(self.get_pending_claims()),
            "uncertain": len(self.get_uncertain_claims()),
            "total_verifications": len(self.verifications),
        }
