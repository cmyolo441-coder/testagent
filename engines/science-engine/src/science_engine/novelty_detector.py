"""Novelty Detector - Detects novelty in scientific claims."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class NoveltyLevel(Enum):
    """Levels of novelty."""
    BREAKTHROUGH = "breakthrough"
    SIGNIFICANT = "significant"
    INCREMENTAL = "incremental"
    MINOR = "minor"
    NONE = "none"
    REPLICATION = "replication"


@dataclass
class NoveltyResult:
    """Result of novelty assessment."""
    claim: str
    novelty_level: NoveltyLevel
    novelty_score: float
    similarity_to_existing: float
    key_differences: List[str]
    potential_impact: str
    existing_prior_art: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "novelty_level": self.novelty_level.value,
            "novelty_score": self.novelty_score,
            "similarity_to_existing": self.similarity_to_existing,
            "key_differences": self.key_differences,
            "potential_impact": self.potential_impact,
            "existing_prior_art": self.existing_prior_art,
        }


class NoveltyDetector:
    """Detects novelty in scientific claims.
    
    Compares new claims against existing knowledge to assess novelty.
    """
    
    def __init__(self):
        self._results: Dict[str, NoveltyResult] = {}
    
    def detect(
        self, claim: str, existing_knowledge: List[str]
    ) -> NoveltyResult:
        """Detect novelty of a claim against existing knowledge.
        
        Args:
            claim: Scientific claim to assess
            existing_knowledge: List of existing known claims/statements
            
        Returns:
            NoveltyResult with novelty assessment
        """
        # Calculate similarity to existing knowledge
        similarities = []
        for known in existing_knowledge:
            sim = self._calculate_similarity(claim, known)
            similarities.append((known, sim))
        
        # Find most similar
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        max_similarity = similarities[0][1] if similarities else 0.0
        avg_similarity = sum(s for _, s in similarities) / len(similarities) if similarities else 0.0
        
        # Extract key differences
        key_differences = self._extract_differences(claim, existing_knowledge)
        
        # Determine novelty level
        novelty_score = 1.0 - max_similarity
        novelty_level = self._determine_novelty_level(novelty_score)
        
        # Assess potential impact
        impact = self._assess_potential_impact(novelty_level, key_differences)
        
        # Prior art
        prior_art = [known for known, sim in similarities[:3] if sim > 0.5]
        
        result = NoveltyResult(
            claim=claim,
            novelty_level=novelty_level,
            novelty_score=novelty_score,
            similarity_to_existing=max_similarity,
            key_differences=key_differences,
            potential_impact=impact,
            existing_prior_art=prior_art,
        )
        
        self._results[claim[:50]] = result
        return result
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate textual similarity."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _extract_differences(self, claim: str, existing: List[str]) -> List[str]:
        """Extract key differences from existing knowledge."""
        differences = []
        
        claim_words = set(claim.lower().split())
        
        for known in existing:
            known_words = set(known.lower().split())
            diff = claim_words - known_words
            if diff and len(diff) > 2:
                differences.append(f"New concepts: {', '.join(list(diff)[:3])}")
        
        return list(set(differences))[:5]
    
    def _determine_novelty_level(self, score: float) -> NoveltyLevel:
        """Determine novelty level from score."""
        if score >= 0.8:
            return NoveltyLevel.BREAKTHROUGH
        elif score >= 0.6:
            return NoveltyLevel.SIGNIFICANT
        elif score >= 0.4:
            return NoveltyLevel.INCREMENTAL
        elif score >= 0.2:
            return NoveltyLevel.MINOR
        else:
            return NoveltyLevel.NONE
    
    def _assess_potential_impact(
        self, level: NoveltyLevel, differences: List[str]
    ) -> str:
        """Assess potential impact."""
        impact_map = {
            NoveltyLevel.BREAKTHROUGH: "High potential to transform the field",
            NoveltyLevel.SIGNIFICANT: "Meaningful contribution to existing knowledge",
            NoveltyLevel.INCREMENTAL: "Useful extension of current understanding",
            NoveltyLevel.MINOR: "Modest addition to the literature",
            NoveltyLevel.NONE: "Largely confirms existing knowledge",
        }
        
        return impact_map.get(level, "Unknown impact")
