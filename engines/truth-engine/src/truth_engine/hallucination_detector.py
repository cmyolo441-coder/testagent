"""Hallucination Detector — Detect potential hallucinations in text"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from enum import Enum
import re
import uuid


class HallucinationType(Enum):
    FACTUAL = "factual"
    STATISTICAL = "statistical"
    CITATION = "citation"
    TEMPORAL = "temporal"
    ENTITY = "entity"
    LOGICAL = "logical"
    SOURCE = "source"


@dataclass
class HallucinationSignal:
    id: str = field(default_factory=lambda: f"HF-{uuid.uuid4().hex[:8]}")
    text_span: str = ""
    hallucination_type: HallucinationType = HallucinationType.FACTUAL
    confidence: float = 0.5
    explanation: str = ""
    severity: str = "medium"
    suggestion: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text_span": self.text_span,
            "type": self.hallucination_type.value,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "severity": self.severity,
            "suggestion": self.suggestion,
        }


class HallucinationDetector:
    """Detect potential hallucinations using multiple heuristic signals."""

    FABRICATED_PATTERNS = [
        (r"according to (?:a |the )?(?:study|report|survey) (?:from )?\d{4}", "Citation without specific source"),
        (r"(?:exactly|precisely) \d+(?:\.\d+)?% (?:of|more|less|fewer)", "Precise statistics without citation"),
        (r"(?:Dr\.|Prof\.) [A-Z][a-z]+ (?:of|at) (?:MIT|Stanford|Harvard|Oxford|Cambridge)", "Fabricated academic attribution"),
        (r"(?:NASA|WHO|CDC|FBI) (?:confirmed|announced|reported|stated)", "Fabricated institutional attribution"),
        (r"(?:always|never|every|all|none|everyone|nobody) (?:does|has|is|can|will)", "Universal claim without qualification"),
    ]

    HEDGING_WORDS = {"maybe", "perhaps", "possibly", "might", "could", "seems", "appears", "suggests"}
    CONFIDENCE_WORDS = {"definitely", "certainly", "always", "never", "proven", "confirmed", "undoubtedly"}
    NUMBERS_RE = re.compile(r"\b\d+(?:\.\d+)?%?\b")

    def __init__(self, knowledge_base: dict[str, str] = None):
        self.knowledge_base = knowledge_base or {}
        self.detected_signals: list[HallucinationSignal] = []

    def detect(self, text: str, context: dict = None) -> list[HallucinationSignal]:
        signals = []
        signals.extend(self._check_fabricated_citations(text))
        signals.extend(self._check_statistical_claims(text))
        signals.extend(self._check_entity_claims(text))
        signals.extend(self._check_temporal_claims(text))
        signals.extend(self._check_universal_claims(text))
        signals.extend(self._check_source_claims(text))
        signals.extend(self._check_knowledge_base(text))
        self.detected_signals.extend(signals)
        return signals

    def detect_with_context(self, text: str, source_text: str = None,
                            knowledge: dict = None) -> list[HallucinationSignal]:
        signals = self.detect(text, {"source": source_text})
        if knowledge:
            self.knowledge_base.update(knowledge)
            signals.extend(self._check_knowledge_base(text))
        return signals

    def get_hallucination_score(self, signals: list[HallucinationSignal]) -> float:
        if not signals:
            return 0.0
        severity_weights = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}
        total = sum(
            s.confidence * severity_weights.get(s.severity, 0.5)
            for s in signals
        )
        return min(1.0, total / max(1, len(signals)))

    def get_summary(self, signals: list[HallucinationSignal] = None) -> dict:
        sigs = signals or self.detected_signals
        by_type = {}
        for s in sigs:
            by_type[s.hallucination_type.value] = by_type.get(s.hallucination_type.value, 0) + 1
        return {
            "total_signals": len(sigs),
            "by_type": by_type,
            "avg_confidence": sum(s.confidence for s in sigs) / len(sigs) if sigs else 0,
            "hallucination_score": self.get_hallucination_score(sigs),
            "severity_breakdown": {
                sev: sum(1 for s in sigs if s.severity == sev)
                for sev in ["low", "medium", "high", "critical"]
            },
        }

    def _check_fabricated_citations(self, text: str) -> list[HallucinationSignal]:
        signals = []
        for pattern, explanation in self.FABRICATED_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                signals.append(HallucinationSignal(
                    text_span=match.group(),
                    hallucination_type=HallucinationType.CITATION,
                    confidence=0.7,
                    explanation=explanation,
                    severity="high",
                    suggestion="Verify the specific source",
                ))
        return signals

    def _check_statistical_claims(self, text: str) -> list[HallucinationSignal]:
        signals = []
        for match in self.NUMBERS_RE.finditer(text):
            num_str = match.group()
            context_start = max(0, match.start() - 50)
            context_end = min(len(text), match.end() + 50)
            context = text[context_start:context_end]
            if "%" in num_str:
                number = float(num_str.replace("%", ""))
                if number > 100 and "%" in num_str:
                    signals.append(HallucinationSignal(
                        text_span=context,
                        hallucination_type=HallucinationType.STATISTICAL,
                        confidence=0.6,
                        explanation=f"Percentage {num_str} exceeds 100%",
                        severity="medium",
                        suggestion="Verify statistical claim",
                    ))
        return signals

    def _check_entity_claims(self, text: str) -> list[HallucinationSignal]:
        signals = []
        known_entities = set(self.knowledge_base.keys())
        words = set(re.findall(r"\b[A-Z][a-z]+\b", text))
        for word in words:
            if word in known_entities:
                context_start = max(0, text.index(word) - 50)
                context_end = min(len(text), text.index(word) + len(word) + 50)
                context = text[context_start:context_end]
                kb_value = self.knowledge_base.get(word, "")
                if kb_value and kb_value.lower() not in context.lower():
                    signals.append(HallucinationSignal(
                        text_span=context,
                        hallucination_type=HallucinationType.ENTITY,
                        confidence=0.4,
                        explanation=f"Entity '{word}' mentioned but may contradict knowledge base",
                        severity="medium",
                        suggestion=f"Verify: KB says {kb_value}",
                    ))
        return signals

    def _check_temporal_claims(self, text: str) -> list[HallucinationSignal]:
        signals = []
        year_pattern = r"\b(19|20)\d{2}\b"
        for match in re.finditer(year_pattern, text):
            year = int(match.group())
            current_year = datetime.now(timezone.utc).year
            if year > current_year + 5:
                signals.append(HallucinationSignal(
                    text_span=match.group(),
                    hallucination_type=HallucinationType.TEMPORAL,
                    confidence=0.5,
                    explanation=f"Future year {year} referenced",
                    severity="low",
                    suggestion="Verify temporal reference",
                ))
        return signals

    def _check_universal_claims(self, text: str) -> list[HallucinationSignal]:
        signals = []
        universals = re.findall(r"\b(always|never|every(?:one|thing|body)|all|none|nobody)\b",
                                text, re.IGNORECASE)
        if universals:
            signals.append(HallucinationSignal(
                text_span=f"Universal quantifiers: {', '.join(set(universals))}",
                hallucination_type=HallucinationType.LOGICAL,
                confidence=0.4,
                explanation="Universal claims are often overstated",
                severity="low",
                suggestion="Consider qualifying universal statements",
            ))
        return signals

    def _check_source_claims(self, text: str) -> list[HallucinationSignal]:
        signals = []
        source_patterns = [
            r"according to (.+?)(?:,|\.|:)",
            r"(?:study|report|research) (?:by|from) (.+?)(?:,|\.|:)",
        ]
        for pattern in source_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                source = match.group(1).strip()
                if len(source) < 3:
                    signals.append(HallucinationSignal(
                        text_span=match.group(),
                        hallucination_type=HallucinationType.SOURCE,
                        confidence=0.3,
                        explanation="Vague or missing source attribution",
                        severity="low",
                        suggestion="Provide specific source",
                    ))
        return signals

    def _check_knowledge_base(self, text: str) -> list[HallucinationSignal]:
        signals = []
        for entity, fact in self.knowledge_base.items():
            if entity.lower() in text.lower():
                if fact.lower() not in text.lower():
                    signals.append(HallucinationSignal(
                        text_span=f"Mention of {entity}",
                        hallucination_type=HallucinationType.FACTUAL,
                        confidence=0.5,
                        explanation=f"Known fact about {entity}: {fact} not reflected",
                        severity="medium",
                        suggestion=f"Cross-reference with: {fact}",
                    ))
        return signals
