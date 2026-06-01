"""Benchmark Against Known Science - Compares claims against established science."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class ConsistencyLevel(Enum):
    """Levels of consistency with known science."""
    FULLY_CONSISTENT = "fully_consistent"
    MOSTLY_CONSISTENT = "mostly_consistent"
    PARTIALLY_CONSISTENT = "partially_consistent"
    INCONSISTENT = "inconsistent"
    CONTRADICTORY = "contradictory"


@dataclass
class BenchmarkResult:
    """Result of benchmarking against known science."""
    claim: str
    consistency_level: ConsistencyLevel
    consistency_score: float
    supporting_evidence: List[str]
    contradicting_evidence: List[str]
    related_theories: List[str]
    gaps_identified: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "consistency_level": self.consistency_level.value,
            "consistency_score": self.consistency_score,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "related_theories": self.related_theories,
            "gaps_identified": self.gaps_identified,
            "recommendations": self.recommendations,
        }


class BenchmarkAgainstKnown:
    """Compares claims against established scientific knowledge."""
    
    # Simplified knowledge base of established science
    KNOWN_SCIENCE = {
        "thermodynamics": [
            "Energy cannot be created or destroyed",
            "Entropy tends to increase in isolated systems",
            "Heat flows from hot to cold",
        ],
        "evolution": [
            "Species evolve through natural selection",
            "Genetic variation drives evolution",
            "Fossil record shows gradual change",
        ],
        "physics": [
            "Light travels at constant speed in vacuum",
            "Mass and energy are equivalent (E=mc^2)",
            "Forces come in pairs (Newton's third law)",
        ],
    }
    
    def __init__(self):
        self._benchmarks: Dict[str, BenchmarkResult] = {}
    
    def benchmark(self, claim: str) -> BenchmarkResult:
        """Benchmark a claim against established science.
        
        Args:
            claim: Scientific claim to benchmark
            
        Returns:
            BenchmarkResult with comparison
        """
        claim_lower = claim.lower()
        
        # Find relevant knowledge
        supporting = []
        contradicting = []
        related = []
        
        for field_name, facts in self.KNOWN_SCIENCE.items():
            for fact in facts:
                similarity = self._calculate_similarity(claim_lower, fact.lower())
                if similarity > 0.5:
                    related.append(fact)
                    if self._is_consistent(claim_lower, fact.lower()):
                        supporting.append(fact)
                    else:
                        contradicting.append(fact)
        
        # Determine consistency level
        consistency_level = self._determine_consistency(
            supporting, contradicting
        )
        
        # Calculate score
        consistency_score = self._calculate_score(supporting, contradicting, related)
        
        # Identify gaps
        gaps = self._identify_gaps(claim)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            consistency_level, contradicting, gaps
        )
        
        result = BenchmarkResult(
            claim=claim,
            consistency_level=consistency_level,
            consistency_score=consistency_score,
            supporting_evidence=supporting[:5],
            contradicting_evidence=contradicting[:5],
            related_theories=related[:5],
            gaps_identified=gaps,
            recommendations=recommendations,
        )
        
        self._benchmarks[claim[:50]] = result
        return result
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between texts."""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _is_consistent(self, claim: str, fact: str) -> bool:
        """Check if claim is consistent with fact."""
        # Simplified consistency check
        contradictory_pairs = [
            ("increase", "decrease"),
            ("always", "never"),
            ("possible", "impossible"),
        ]
        
        for word1, word2 in contradictory_pairs:
            if (word1 in claim and word2 in fact) or (word2 in claim and word1 in fact):
                return False
        
        return True
    
    def _determine_consistency(
        self, supporting: List[str], contradicting: List[str]
    ) -> ConsistencyLevel:
        """Determine consistency level."""
        total = len(supporting) + len(contradicting)
        
        if total == 0:
            return ConsistencyLevel.PARTIALLY_CONSISTENT
        
        support_ratio = len(supporting) / total
        
        if support_ratio >= 0.9:
            return ConsistencyLevel.FULLY_CONSISTENT
        elif support_ratio >= 0.7:
            return ConsistencyLevel.MOSTLY_CONSISTENT
        elif support_ratio >= 0.4:
            return ConsistencyLevel.PARTIALLY_CONSISTENT
        elif support_ratio >= 0.2:
            return ConsistencyLevel.INCONSISTENT
        else:
            return ConsistencyLevel.CONTRADICTORY
    
    def _calculate_score(
        self,
        supporting: List[str],
        contradicting: List[str],
        related: List[str],
    ) -> float:
        """Calculate consistency score."""
        if not related:
            return 0.5  # Neutral score for untested claims
        
        support_score = len(supporting) / max(len(related), 1)
        contradiction_penalty = len(contradicting) * 0.2
        
        return max(0, min(1, support_score - contradiction_penalty))
    
    def _identify_gaps(self, claim: str) -> List[str]:
        """Identify gaps in relation to known science."""
        gaps = []
        
        claim_words = set(claim.lower().split())
        
        for field_name, facts in self.KNOWN_SCIENCE.items():
            field_words = set(field_name.split())
            if not (claim_words & field_words):
                continue
            
            for fact in facts:
                fact_words = set(fact.lower().split())
                overlap = claim_words & fact_words
                if 0 < len(overlap) < len(fact_words) / 2:
                    gaps.append(f"Partial coverage of {field_name}: {fact[:50]}")
        
        return list(set(gaps))[:3]
    
    def _generate_recommendations(
        self,
        level: ConsistencyLevel,
        contradicting: List[str],
        gaps: List[str],
    ) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        if level == ConsistencyLevel.FULLY_CONSISTENT:
            recommendations.append("Claim is well-aligned with established science")
        elif level == ConsistencyLevel.MOSTLY_CONSISTENT:
            recommendations.append("Minor adjustments may be needed for full consistency")
        elif level == ConsistencyLevel.PARTIALLY_CONSISTENT:
            recommendations.append("Significant revision needed to align with known science")
        elif level in [ConsistencyLevel.INCONSISTENT, ConsistencyLevel.CONTRADICTORY]:
            recommendations.append("Fundamental issues with claim relative to established science")
        
        if contradicting:
            recommendations.append("Address contradicting evidence before publishing")
        
        if gaps:
            recommendations.append("Consider broader scientific context")
        
        return recommendations[:3]
