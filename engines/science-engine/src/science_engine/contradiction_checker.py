"""Contradiction Checker - Checks for contradictions between hypotheses and known facts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class ContradictionType(Enum):
    """Types of contradictions."""
    LOGICAL = "logical"
    EMPIRICAL = "empirical"
    MATHEMATICAL = "mathematical"
    CONCEPTUAL = "conceptual"
    DEFINITIONAL = "definitional"


@dataclass
class Contradiction:
    """A detected contradiction."""
    statement1: str
    statement2: str
    contradiction_type: ContradictionType
    severity: float
    explanation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "statement1": self.statement1,
            "statement2": self.statement2,
            "contradiction_type": self.contradiction_type.value,
            "severity": self.severity,
            "explanation": self.explanation,
        }


@dataclass
class ContradictionResult:
    """Result of contradiction checking."""
    hypothesis: str
    contradictions_found: bool
    contradictions: List[Contradiction]
    consistency_score: float
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis": self.hypothesis,
            "contradictions_found": self.contradictions_found,
            "contradictions": [c.to_dict() for c in self.contradictions],
            "consistency_score": self.consistency_score,
            "recommendations": self.recommendations,
        }


class ContradictionChecker:
    """Checks for contradictions between hypotheses and known facts."""
    
    def __init__(self):
        self._results: Dict[str, ContradictionResult] = {}
    
    def check(
        self, hypothesis: Dict[str, Any], known_facts: List[str]
    ) -> ContradictionResult:
        """Check hypothesis against known facts for contradictions.
        
        Args:
            hypothesis: Hypothesis dictionary
            known_facts: List of known facts/statements
            
        Returns:
            ContradictionResult with contradiction analysis
        """
        hyp_statement = hypothesis.get("statement", "")
        hyp_assumptions = hypothesis.get("assumptions", [])
        
        contradictions = []
        
        # Check logical contradictions
        for fact in known_facts:
            contradiction = self._check_logical_contradiction(hyp_statement, fact)
            if contradiction:
                contradictions.append(contradiction)
        
        # Check assumption contradictions
        for assumption in hyp_assumptions:
            for fact in known_facts:
                contradiction = self._check_assumption_contradiction(assumption, fact)
                if contradiction:
                    contradictions.append(contradiction)
        
        # Check empirical contradictions
        for fact in known_facts:
            contradiction = self._check_empirical_contradiction(hyp_statement, fact)
            if contradiction:
                contradictions.append(contradiction)
        
        # Calculate consistency score
        consistency = self._calculate_consistency(contradictions)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(contradictions)
        
        result = ContradictionResult(
            hypothesis=hyp_statement,
            contradictions_found=len(contradictions) > 0,
            contradictions=contradictions,
            consistency_score=consistency,
            recommendations=recommendations,
        )
        
        self._results[hyp_statement[:50]] = result
        return result
    
    def _check_logical_contradiction(
        self, statement1: str, statement2: str
    ) -> Optional[Contradiction]:
        """Check for logical contradictions."""
        s1 = statement1.lower()
        s2 = statement2.lower()
        
        contradictory_pairs = [
            ("always", "never"),
            ("all", "none"),
            ("increase", "decrease"),
            ("positive", "negative"),
            ("cause", "prevent"),
            ("supports", "contradicts"),
        ]
        
        for word1, word2 in contradictory_pairs:
            if (word1 in s1 and word2 in s2) or (word2 in s1 and word1 in s2):
                # Check if discussing similar topic
                words1 = set(s1.split())
                words2 = set(s2.split())
                overlap = words1 & words2
                
                if len(overlap) > 2:
                    return Contradiction(
                        statement1=statement1,
                        statement2=statement2,
                        contradiction_type=ContradictionType.LOGICAL,
                        severity=0.7,
                        explanation=f"Contradictory claims using '{word1}' vs '{word2}'",
                    )
        
        return None
    
    def _check_assumption_contradiction(
        self, assumption: str, fact: str
    ) -> Optional[Contradiction]:
        """Check if assumption contradicts a known fact."""
        a = assumption.lower()
        f = fact.lower()
        
        # Check for direct negation
        if f"not {a}" in f or f"not {f}" in a:
            return Contradiction(
                statement1=assumption,
                statement2=fact,
                contradiction_type=ContradictionType.CONCEPTUAL,
                severity=0.8,
                explanation="Assumption directly contradicts known fact",
            )
        
        return None
    
    def _check_empirical_contradiction(
        self, hypothesis: str, fact: str
    ) -> Optional[Contradiction]:
        """Check for empirical contradictions."""
        h = hypothesis.lower()
        f = fact.lower()
        
        # Check for conflicting empirical claims
        empirical_patterns = [
            ("observed", "not observed"),
            ("measured", "not measured"),
            ("confirmed", "not confirmed"),
            ("found", "not found"),
        ]
        
        for pos, neg in empirical_patterns:
            if (pos in h and neg in f) or (neg in h and pos in f):
                return Contradiction(
                    statement1=hypothesis,
                    statement2=fact,
                    contradiction_type=ContradictionType.EMPIRICAL,
                    severity=0.6,
                    explanation=f"Conflicting empirical claims: {pos} vs {neg}",
                )
        
        return None
    
    def _calculate_consistency(self, contradictions: List[Contradiction]) -> float:
        """Calculate consistency score."""
        if not contradictions:
            return 1.0
        
        severity_sum = sum(c.severity for c in contradictions)
        max_possible = len(contradictions) * 1.0
        
        return max(0, 1.0 - severity_sum / max_possible)
    
    def _generate_recommendations(self, contradictions: List[Contradiction]) -> List[str]:
        """Generate recommendations based on contradictions."""
        if not contradictions:
            return ["No contradictions found - hypothesis is consistent with known facts"]
        
        recommendations = []
        
        for c in contradictions[:3]:
            if c.contradiction_type == ContradictionType.LOGICAL:
                recommendations.append("Review logical consistency of claims")
            elif c.contradiction_type == ContradictionType.EMPIRICAL:
                recommendations.append("Compare empirical evidence carefully")
            elif c.contradiction_type == ContradictionType.CONCEPTUAL:
                recommendations.append("Clarify conceptual definitions")
        
        if len(contradictions) > 3:
            recommendations.append("Consider fundamental revision of hypothesis")
        
        return recommendations
