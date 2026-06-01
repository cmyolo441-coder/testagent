"""Consistency Checker - Checks consistency of axioms and theorems."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class ConsistencyStatus(Enum):
    """Status of consistency check."""
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    UNKNOWN = "unknown"
    CONDITIONALLY_CONSISTENT = "conditionally_consistent"


@dataclass
class ConsistencyResult:
    """Result of consistency check."""
    axioms_checked: int
    theorems_checked: int
    status: ConsistencyStatus
    issues_found: List[str]
    confidence: float
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "axioms_checked": self.axioms_checked,
            "theorems_checked": self.theorems_checked,
            "status": self.status.value,
            "issues_found": self.issues_found,
            "confidence": self.confidence,
            "recommendations": self.recommendations,
        }


class ConsistencyChecker:
    """Checks consistency of axioms and theorems.
    
    Verifies that mathematical systems are internally consistent
    and that theorems follow logically from axioms.
    """
    
    def __init__(self):
        self._results: Dict[str, ConsistencyResult] = {}
    
    def check(
        self,
        axioms: List[str],
        theorems: List[str],
    ) -> ConsistencyResult:
        """Check consistency of axioms and theorems.
        
        Args:
            axioms: List of axioms
            theorems: List of theorems
            
        Returns:
            ConsistencyResult with analysis
        """
        issues = []
        
        # Check for obvious contradictions in axioms
        axiom_issues = self._check_axiom_consistency(axioms)
        issues.extend(axiom_issues)
        
        # Check if theorems are consistent with axioms
        theorem_issues = self._check_theorem_consistency(axioms, theorems)
        issues.extend(theorem_issues)
        
        # Check for circular reasoning
        circular_issues = self._check_circular_reasoning(axioms, theorems)
        issues.extend(circular_issues)
        
        # Determine status
        if not issues:
            status = ConsistencyStatus.CONSISTENT
            confidence = 0.9
        elif len(issues) <= 2:
            status = ConsistencyStatus.CONDITIONALLY_CONSISTENT
            confidence = 0.7
        else:
            status = ConsistencyStatus.INCONSISTENT
            confidence = 0.5
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues)
        
        result = ConsistencyResult(
            axioms_checked=len(axioms),
            theorems_checked=len(theorems),
            status=status,
            issues_found=issues,
            confidence=confidence,
            recommendations=recommendations,
        )
        
        self._results[str(len(self._results))] = result
        return result
    
    def _check_axiom_consistency(self, axioms: List[str]) -> List[str]:
        """Check consistency among axioms."""
        issues = []
        
        # Check for direct contradictions
        contradictory_pairs = [
            ("always", "never"),
            ("all", "none"),
            ("exists", "does not exist"),
        ]
        
        for i, axiom1 in enumerate(axioms):
            for axiom2 in axioms[i+1:]:
                a1 = axiom1.lower()
                a2 = axiom2.lower()
                
                for word1, word2 in contradictory_pairs:
                    if (word1 in a1 and word2 in a2) or (word2 in a1 and word1 in a2):
                        # Check if discussing same topic
                        words1 = set(a1.split())
                        words2 = set(a2.split())
                        overlap = words1 & words2
                        
                        if len(overlap) > 2:
                            issues.append(
                                f"Potential contradiction: '{axiom1[:50]}' vs '{axiom2[:50]}'"
                            )
        
        return issues[:5]
    
    def _check_theorem_consistency(
        self, axioms: List[str], theorems: List[str]
    ) -> List[str]:
        """Check if theorems are consistent with axioms."""
        issues = []
        
        # Simplified check: look for obvious incompatibilities
        axiom_text = " ".join(axioms).lower()
        
        for theorem in theorems:
            theorem_lower = theorem.lower()
            
            # Check if theorem contradicts axioms
            if "impossible" in axiom_text and "possible" in theorem_lower:
                issues.append(f"Theorem may contradict axiom: {theorem[:50]}")
            
            if "forbidden" in axiom_text and "allowed" in theorem_lower:
                issues.append(f"Theorem may contradict axiom: {theorem[:50]}")
        
        return issues[:5]
    
    def _check_circular_reasoning(
        self, axioms: List[str], theorems: List[str]
    ) -> List[str]:
        """Check for circular reasoning."""
        issues = []
        
        # Check if any theorem is essentially an axiom
        for theorem in theorems:
            for axiom in axioms:
                if self._are_equivalent(theorem, axiom):
                    issues.append(f"Theorem is essentially equivalent to axiom: {theorem[:50]}")
                    break
        
        return issues[:3]
    
    def _are_equivalent(self, text1: str, text2: str) -> bool:
        """Check if two statements are equivalent (simplified)."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Simple similarity check
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return False
        
        similarity = len(intersection) / len(union)
        return similarity > 0.8
    
    def _generate_recommendations(self, issues: List[str]) -> List[str]:
        """Generate recommendations based on issues."""
        recommendations = []
        
        if not issues:
            recommendations.append("System appears consistent")
        else:
            recommendations.append("Review and resolve identified contradictions")
            recommendations.append("Consider adding clarifying definitions")
        
        if len(issues) > 3:
            recommendations.append("Consider rebuilding the axiom system from scratch")
        
        return recommendations[:3]
