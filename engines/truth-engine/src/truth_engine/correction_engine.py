"""Correction Engine — Detect and correct errors in text"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable
from enum import Enum
import uuid
import re


class CorrectionType(Enum):
    FACTUAL = "factual"
    GRAMMATICAL = "grammatical"
    NUMERICAL = "numerical"
    LOGICAL = "logical"
    CITATION = "citation"
    TEMPORAL = "temporal"
    CONSISTENCY = "consistency"


@dataclass
class Correction:
    id: str = field(default_factory=lambda: f"COR-{uuid.uuid4().hex[:8]}")
    original_text: str = ""
    corrected_text: str = ""
    correction_type: CorrectionType = CorrectionType.FACTUAL
    confidence: float = 0.5
    explanation: str = ""
    location: tuple = (0, 0)
    applied: bool = False
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "original": self.original_text,
            "corrected": self.corrected_text,
            "type": self.correction_type.value,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "applied": self.applied,
        }


@dataclass
class CorrectionResult:
    text: str = ""
    corrections: list[Correction] = field(default_factory=list)
    applied_count: int = 0
    remaining_issues: int = 0
    confidence_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "corrections": [c.to_dict() for c in self.corrections],
            "applied": self.applied_count,
            "remaining": self.remaining_issues,
            "confidence": f"{self.confidence_score:.2f}",
        }


class CorrectionEngine:
    """Detect and correct errors in text using multiple strategies."""

    def __init__(self, fact_checker: Optional[Callable] = None,
                 grammar_checker: Optional[Callable] = None):
        self.fact_checker = fact_checker or self._default_fact_checker
        self.grammar_checker = grammar_checker or self._default_grammar_checker
        self.corrections_history: list[Correction] = []
        self.correction_rules: list[Callable] = [
            self._check_numerical_consistency,
            self._check_logical_consistency,
            self._check_temporal_consistency,
        ]

    def detect_and_correct(self, text: str, context: dict = None) -> CorrectionResult:
        result = CorrectionResult(text=text)
        # Run all correction checkers
        for rule in self.correction_rules:
            corrections = rule(text, context or {})
            result.corrections.extend(corrections)
        # Apply high-confidence corrections
        corrected_text = text
        for correction in result.corrections:
            if correction.confidence >= 0.7:
                corrected_text = corrected_text.replace(
                    correction.original_text, correction.corrected_text
                )
                correction.applied = True
                result.applied_count += 1
        result.text = corrected_text
        result.remaining_issues = sum(1 for c in result.corrections if not c.applied)
        result.confidence_score = self._calculate_confidence(result.corrections)
        self.corrections_history.extend(result.corrections)
        return result

    def apply_correction(self, text: str, correction: Correction) -> str:
        if correction.confidence >= 0.5:
            corrected = text.replace(correction.original_text, correction.corrected_text)
            correction.applied = True
            return corrected
        return text

    def batch_correct(self, texts: list[str], context: dict = None) -> list[CorrectionResult]:
        return [self.detect_and_correct(t, context) for t in texts]

    def get_correction_suggestions(self, text: str) -> list[dict]:
        corrections = []
        for rule in self.correction_rules:
            rule_corrections = rule(text, {})
            corrections.extend([c.to_dict() for c in rule_corrections])
        return sorted(corrections, key=lambda c: c["confidence"], reverse=True)

    def get_correction_stats(self) -> dict:
        history = self.corrections_history
        by_type = {}
        for c in history:
            by_type[c.correction_type.value] = by_type.get(c.correction_type.value, 0) + 1
        return {
            "total_corrections": len(history),
            "applied": sum(1 for c in history if c.applied),
            "by_type": by_type,
            "avg_confidence": sum(c.confidence for c in history) / len(history) if history else 0,
        }

    def _check_numerical_consistency(self, text: str, context: dict) -> list[Correction]:
        corrections = []
        numbers = re.findall(r"\b\d+(?:\.\d+)?%?\b", text)
        if len(numbers) > 1:
            parsed = []
            for n in numbers:
                try:
                    parsed.append(float(n.replace("%", "")))
                except ValueError:
                    pass
            if parsed:
                mean = sum(parsed) / len(parsed)
                for i, (num_str, num_val) in enumerate(zip(numbers, parsed)):
                    if num_val > mean * 10 or (mean > 0 and num_val < mean / 10):
                        corrections.append(Correction(
                            original_text=num_str,
                            corrected_text=num_str,
                            correction_type=CorrectionType.NUMERICAL,
                            confidence=0.4,
                            explanation=f"Number {num_str} is an outlier compared to other values",
                        ))
        return corrections

    def _check_logical_consistency(self, text: str, context: dict) -> list[Correction]:
        corrections = []
        contradiction_pairs = [
            (r"\b(increase|rise|grow)\b", r"\b(decrease|fall|decline)\b"),
            (r"\b(always|never)\b", r"\b(sometimes|often|rarely)\b"),
            (r"\b(all|every)\b", r"\b(none|no)\b"),
        ]
        for pattern1, pattern2 in contradiction_pairs:
            match1 = re.search(pattern1, text, re.IGNORECASE)
            match2 = re.search(pattern2, text, re.IGNORECASE)
            if match1 and match2:
                corrections.append(Correction(
                    original_text=f"{match1.group()} ... {match2.group()}",
                    corrected_text=f"{match1.group()} ... {match2.group()}",
                    correction_type=CorrectionType.LOGICAL,
                    confidence=0.3,
                    explanation="Potentially contradictory terms in same context",
                ))
        return corrections

    def _check_temporal_consistency(self, text: str, context: dict) -> list[Correction]:
        corrections = []
        past_indicators = ["was", "were", "did", "had", "before"]
        future_indicators = ["will", "shall", "tomorrow", "next"]
        has_past = any(w in text.lower().split() for w in past_indicators)
        has_future = any(w in text.lower().split() for w in future_indicators)
        if has_past and has_future:
            corrections.append(Correction(
                original_text=text[:100],
                corrected_text=text[:100],
                correction_type=CorrectionType.TEMPORAL,
                confidence=0.2,
                explanation="Mixed temporal references",
            ))
        return corrections

    @staticmethod
    def _default_fact_checker(text: str, context: dict) -> dict:
        return {"consistent": True, "confidence": 0.5}

    @staticmethod
    def _default_grammar_checker(text: str) -> list[dict]:
        return []

    def _calculate_confidence(self, corrections: list[Correction]) -> float:
        if not corrections:
            return 1.0
        applied = [c for c in corrections if c.applied]
        if not applied:
            return 0.8
        return sum(c.confidence for c in applied) / len(applied)
