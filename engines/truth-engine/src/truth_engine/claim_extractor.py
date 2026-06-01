"""Claim Extractor — Extract checkable claims from text"""
import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ClaimType(Enum):
    FACTUAL = "factual"
    PREDICTION = "prediction"
    OPINION = "opinion"
    DEFINITION = "definition"
    STATISTICAL = "statistical"
    CAUSAL = "causal"
    COMPARATIVE = "comparative"
    TEMPORAL = "temporal"


class ClaimConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


@dataclass
class Claim:
    id: str
    text: str
    claim_type: ClaimType
    confidence: ClaimConfidence = ClaimConfidence.MEDIUM
    verifiable: bool = True
    subject: str = ""
    predicate: str = ""
    object: str = ""
    sources: list[str] = field(default_factory=list)
    verification_level: int = 0  # 0-5
    context: str = ""
    negated: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "type": self.claim_type.value,
            "confidence": self.confidence.value,
            "verifiable": self.verifiable,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "verification_level": self.verification_level,
            "negated": self.negated,
        }


class ClaimExtractor:
    """Extract checkable claims from text output."""

    CLAIM_PATTERNS = {
        ClaimType.FACTUAL: [
            r"(?:is|are|was|were)\s+(?:a|an|the)?\s*\w+",
            r"(?:has|have|had)\s+\w+",
            r"(?:can|could|will|would|shall|should|may|might)\s+\w+",
            r"\w+\s+(?:equals?|is equal to|is approximately)\s+[\d.]+",
        ],
        ClaimType.STATISTICAL: [
            r"\d+(?:\.\d+)?%",
            r"\d+(?:\.\d+)?\s*(?:times|fold|percent|percentile)",
            r"approximately\s+\d+",
            r"about\s+\d+(?:\.\d+)?",
        ],
        ClaimType.CAUSAL: [
            r"(?:because|since|as|due to|caused by|results? in|leads? to)",
            r"(?:if|when)\s+.+,\s+then",
            r"(?:causes?|prevents?|increases?|decreases?)\s+",
        ],
        ClaimType.COMPARATIVE: [
            r"(?:more|less|greater|smaller|better|worse|faster|slower)\s+than",
            r"(?:most|least|best|worst|fastest|slowest)\s+\w+",
            r"(?:compared to|relative to|versus|vs\.?)\s+",
        ],
        ClaimType.TEMPORAL: [
            r"(?:before|after|during|while|since|until)\s+",
            r"(?:always|never|sometimes|often|rarely|frequently)\s+",
            r"(?:first|last|next|previous|current)\s+",
        ],
    }

    NEGATION_WORDS = {"not", "no", "never", "neither", "nor", "none", "nothing"}

    def extract_claims(self, text: str) -> list[Claim]:
        claims = []
        claim_id = 0

        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue

            detected_type = self._detect_claim_type(sentence)
            if detected_type:
                negated = self._detect_negation(sentence)
                confidence = self._assess_confidence(sentence)
                verifiable = confidence != ClaimConfidence.UNCERTAIN

                claim = Claim(
                    id=f"CLAIM-{claim_id:04d}",
                    text=sentence,
                    claim_type=detected_type,
                    confidence=confidence,
                    verifiable=verifiable,
                    negated=negated,
                )
                claims.append(claim)
                claim_id += 1

        return claims

    def _detect_claim_type(self, sentence: str) -> Optional[ClaimType]:
        for claim_type, patterns in self.CLAIM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    return claim_type
        return None

    def _detect_negation(self, sentence: str) -> bool:
        words = sentence.lower().split()
        return any(w in self.NEGATION_WORDS for w in words)

    def _assess_confidence(self, sentence: str) -> ClaimConfidence:
        high_conf_words = {"definitely", "certainly", "always", "never", "proven", "confirmed"}
        low_conf_words = {"maybe", "perhaps", "possibly", "might", "could", "seems", "appears"}
        medium_conf_words = {"usually", "generally", "often", "likely", "probably"}

        words = set(sentence.lower().split())
        if words & high_conf_words:
            return ClaimConfidence.HIGH
        if words & low_conf_words:
            return ClaimConfidence.LOW
        if words & medium_conf_words:
            return ClaimConfidence.MEDIUM
        return ClaimConfidence.MEDIUM

    def extract_verifiable_claims(self, text: str) -> list[Claim]:
        claims = self.extract_claims(text)
        return [c for c in claims if c.verifiable]

    def get_claim_summary(self, claims: list[Claim]) -> dict:
        by_type = {}
        for c in claims:
            by_type[c.claim_type.value] = by_type.get(c.claim_type.value, 0) + 1
        return {
            "total_claims": len(claims),
            "verifiable": len([c for c in claims if c.verifiable]),
            "by_type": by_type,
            "negated": len([c for c in claims if c.negated]),
        }
