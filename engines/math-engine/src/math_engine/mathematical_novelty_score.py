"""Mathematical Novelty Score - Scores novelty of mathematical contributions."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class NoveltyLevel(Enum):
    """Levels of mathematical novelty."""
    BREAKTHROUGH = "breakthrough"
    SIGNIFICANT = "significant"
    MODERATE = "moderate"
    MINIMAL = "minimal"
    INCREMENTAL = "incremental"
    NONE = "none"


@dataclass
class NoveltyAssessment:
    """Assessment of mathematical novelty."""
    contribution: str
    novelty_level: NoveltyLevel
    novelty_score: float
    originality_score: float
    significance_score: float
    technical_depth: float
    comparison_to_existing: List[str]
    potential_impact: str
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "contribution": self.contribution[:100],
            "novelty_level": self.novelty_level.value,
            "novelty_score": self.novelty_score,
            "originality_score": self.originality_score,
            "significance_score": self.significance_score,
            "technical_depth": self.technical_depth,
            "comparison_to_existing": self.comparison_to_existing,
            "potential_impact": self.potential_impact,
            "recommendations": self.recommendations,
        }


class MathematicalNoveltyScore:
    """Scores novelty of mathematical contributions.
    
    Evaluates the originality, significance, and technical depth
    of mathematical results.
    """
    
    # Simplified knowledge base of existing results
    KNOWN_RESULTS = [
        "Pythagorean theorem",
        "Fermat's Last Theorem",
        "Euler's formula",
        "Fundamental Theorem of Calculus",
        "Cantor's theorem",
        "Gödel's incompleteness theorems",
    ]
    
    def __init__(self):
        self._assessments: Dict[str, NoveltyAssessment] = {}
    
    def score(self, contribution: Dict[str, Any]) -> NoveltyAssessment:
        """Score the novelty of a mathematical contribution.
        
        Args:
            contribution: Mathematical contribution to assess
            
        Returns:
            NoveltyAssessment with scores
        """
        statement = contribution.get("statement", "")
        field_name = contribution.get("field", "")
        
        # Calculate originality
        originality = self._calculate_originality(statement, field_name)
        
        # Calculate significance
        significance = self._calculate_significance(contribution)
        
        # Calculate technical depth
        depth = self._calculate_technical_depth(contribution)
        
        # Overall novelty score
        novelty_score = (originality * 0.4 + significance * 0.35 + depth * 0.25)
        
        # Determine level
        novelty_level = self._determine_level(novelty_score)
        
        # Compare to existing
        comparison = self._compare_to_existing(statement)
        
        # Assess impact
        impact = self._assess_potential_impact(novelty_level, field_name)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(novelty_level, originality)
        
        assessment = NoveltyAssessment(
            contribution=statement,
            novelty_level=novelty_level,
            novelty_score=novelty_score,
            originality_score=originality,
            significance_score=significance,
            technical_depth=depth,
            comparison_to_existing=comparison,
            potential_impact=impact,
            recommendations=recommendations,
        )
        
        self._assessments[statement[:50]] = assessment
        return assessment
    
    def _calculate_originality(self, statement: str, field_name: str) -> float:
        """Calculate originality score."""
        score = 0.5
        
        # Check similarity to known results
        for known in self.KNOWN_RESULTS:
            similarity = self._text_similarity(statement.lower(), known.lower())
            if similarity > 0.5:
                score -= 0.1
        
        # Boost for new fields or combinations
        if field_name and field_name not in ["general", "basic"]:
            score += 0.1
        
        # Boost for novel terminology
        novel_terms = ["new", "novel", "first", "unprecedented", "original"]
        if any(term in statement.lower() for term in novel_terms):
            score += 0.1
        
        return max(0.1, min(score, 1.0))
    
    def _calculate_significance(self, contribution: Dict[str, Any]) -> float:
        """Calculate significance score."""
        score = 0.5
        
        # Check for important keywords
        significant_keywords = [
            "prove", "theorem", "fundamental", "general",
            "new class", "unified", "generalization"
        ]
        
        statement = contribution.get("statement", "").lower()
        for keyword in significant_keywords:
            if keyword in statement:
                score += 0.05
        
        # Check if addresses open problem
        if contribution.get("addresses_open_problem", False):
            score += 0.2
        
        # Check for applications
        if contribution.get("has_applications", False):
            score += 0.1
        
        return max(0.1, min(score, 1.0))
    
    def _calculate_technical_depth(self, contribution: Dict[str, Any]) -> float:
        """Calculate technical depth."""
        score = 0.5
        
        # Check for technical sophistication
        technical_terms = [
            "proof", "construction", "algorithm", "bound",
            "asymptotic", "convergence", "optimization"
        ]
        
        statement = contribution.get("statement", "").lower()
        for term in technical_terms:
            if term in statement:
                score += 0.05
        
        # Check proof complexity
        proof_steps = contribution.get("proof_steps", 0)
        if proof_steps > 10:
            score += 0.1
        if proof_steps > 50:
            score += 0.1
        
        return max(0.1, min(score, 1.0))
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity."""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _determine_level(self, score: float) -> NoveltyLevel:
        """Determine novelty level from score."""
        if score >= 0.9:
            return NoveltyLevel.BREAKTHROUGH
        elif score >= 0.75:
            return NoveltyLevel.SIGNIFICANT
        elif score >= 0.6:
            return NoveltyLevel.MODERATE
        elif score >= 0.4:
            return NoveltyLevel.MINIMAL
        elif score >= 0.2:
            return NoveltyLevel.INCREMENTAL
        else:
            return NoveltyLevel.NONE
    
    def _compare_to_existing(self, statement: str) -> List[str]:
        """Compare to existing results."""
        comparisons = []
        
        for known in self.KNOWN_RESULTS:
            similarity = self._text_similarity(statement.lower(), known.lower())
            if similarity > 0.3:
                comparisons.append(f"Related to {known} (similarity: {similarity:.2f})")
        
        if not comparisons:
            comparisons.append("No close match to known results found")
        
        return comparisons[:3]
    
    def _assess_potential_impact(self, level: NoveltyLevel, field_name: str) -> str:
        """Assess potential impact."""
        impact_map = {
            NoveltyLevel.BREAKTHROUGH: f"Potential to transform {field_name} mathematics",
            NoveltyLevel.SIGNIFICANT: f"Significant advancement in {field_name}",
            NoveltyLevel.MODERATE: f"Useful contribution to {field_name}",
            NoveltyLevel.MINIMAL: f"Modest addition to {field_name} literature",
            NoveltyLevel.INCREMENTAL: "Small improvement to existing results",
            NoveltyLevel.NONE: "Confirms existing knowledge",
        }
        
        return impact_map.get(level, "Impact unclear")
    
    def _generate_recommendations(
        self, level: NoveltyLevel, originality: float
    ) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        if level in [NoveltyLevel.BREAKTHROUGH, NoveltyLevel.SIGNIFICANT]:
            recommendations.append("Consider submitting to top-tier journal")
            recommendations.append("Prepare for peer review scrutiny")
        elif level == NoveltyLevel.MODERATE:
            recommendations.append("Submit to appropriate specialized journal")
        else:
            recommendations.append("Consider positioning relative to existing work")
        
        if originality < 0.5:
            recommendations.append("Better distinguish from prior art")
        
        return recommendations[:2]
