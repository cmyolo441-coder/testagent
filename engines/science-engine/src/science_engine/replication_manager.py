"""Replication Manager - Manages replication of scientific experiments."""

from __future__ import annotations

import hashlib
import random
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


class ReplicationType(Enum):
    """Types of replication."""
    DIRECT = "direct"
    CLOSE = "close"
    CONCEPTUAL = "conceptual"
    PARTIAL = "partial"
    FAILURE = "failure"


class ReplicationStatus(Enum):
    """Status of replication."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"


@dataclass
class ReplicationResults:
    """Results of a replication attempt."""
    original_study_id: str
    replication_study_id: str
    replication_type: ReplicationType
    status: ReplicationStatus
    original_effect_size: float
    replication_effect_size: float
    effect_size_ratio: float
    original_significant: bool
    replication_significant: bool
    concordance: bool
    methodological_differences: List[str]
    similarity_score: float
    confidence_in_original: float
    recommendation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_study_id": self.original_study_id,
            "replication_study_id": self.replication_study_id,
            "replication_type": self.replication_type.value,
            "status": self.status.value,
            "original_effect_size": self.original_effect_size,
            "replication_effect_size": self.replication_effect_size,
            "effect_size_ratio": self.effect_size_ratio,
            "original_significant": self.original_significant,
            "replication_significant": self.replication_significant,
            "concordance": self.concordance,
            "methodological_differences": self.methodological_differences,
            "similarity_score": self.similarity_score,
            "confidence_in_original": self.confidence_in_original,
            "recommendation": self.recommendation,
        }


class ReplicationManager:
    """Manages replication of scientific experiments.
    
    Designs and evaluates replications to assess the reliability
    of scientific findings.
    """
    
    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._replications: Dict[str, ReplicationResults] = {}
        self._counter = 0
    
    def replicate(self, experiment: Dict[str, Any]) -> ReplicationResults:
        """Perform replication of an experiment.
        
        Args:
            experiment: Original experiment data
            
        Returns:
            ReplicationResults comparing original and replication
        """
        self._counter += 1
        
        original_id = experiment.get("id", "unknown")
        
        # Extract original results
        original_effect = experiment.get("effect_size", 0.5)
        original_significant = experiment.get("significant", True)
        original_sample = experiment.get("sample_size", 30)
        methodology = experiment.get("methodology", {})
        
        # Determine replication type
        rep_type = self._determine_replication_type(experiment)
        
        # Simulate replication
        rep_effect, rep_significant, differences = self._simulate_replication(
            original_effect, original_sample, rep_type, methodology
        )
        
        # Calculate concordance
        effect_ratio = rep_effect / original_effect if original_effect != 0 else 0
        concordance = (
            rep_significant == original_significant and
            0.5 < effect_ratio < 2.0
        )
        
        # Calculate similarity score
        similarity = self._calculate_similarity_score(
            original_effect, rep_effect, differences
        )
        
        # Assess confidence
        confidence = self._assess_confidence(
            concordance, similarity, rep_type, effect_ratio
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            concordance, similarity, rep_type, confidence
        )
        
        rep_id = f"REP-{hashlib.md5(f'{original_id}{self._counter}'.encode()).hexdigest()[:8].upper()}"
        
        results = ReplicationResults(
            original_study_id=original_id,
            replication_study_id=rep_id,
            replication_type=rep_type,
            status=ReplicationStatus.COMPLETED if concordance else ReplicationStatus.INCONCLUSIVE,
            original_effect_size=original_effect,
            replication_effect_size=rep_effect,
            effect_size_ratio=effect_ratio,
            original_significant=original_significant,
            replication_significant=rep_significant,
            concordance=concordance,
            methodological_differences=differences,
            similarity_score=similarity,
            confidence_in_original=confidence,
            recommendation=recommendation,
        )
        
        self._replications[rep_id] = results
        return results
    
    def _determine_replication_type(self, experiment: Dict[str, Any]) -> ReplicationType:
        """Determine appropriate replication type."""
        sample_size = experiment.get("sample_size", 30)
        methodology = experiment.get("methodology", {})
        
        # Determine based on available resources and methodology
        if sample_size >= 100 and methodology.get("detailed_protocol", False):
            return ReplicationType.DIRECT
        elif sample_size >= 50:
            return ReplicationType.CLOSE
        elif methodology.get("conceptual_only", False):
            return ReplicationType.CONCEPTUAL
        else:
            return ReplicationType.PARTIAL
    
    def _simulate_replication(
        self,
        original_effect: float,
        original_sample: int,
        rep_type: ReplicationType,
        methodology: Dict[str, Any],
    ) -> Tuple[float, bool, List[str]]:
        """Simulate replication study."""
        differences = []
        
        # Effect size variation based on replication type
        variation_factors = {
            ReplicationType.DIRECT: 0.1,
            ReplicationType.CLOSE: 0.2,
            ReplicationType.CONCEPTUAL: 0.4,
            ReplicationType.PARTIAL: 0.3,
        }
        
        variation = variation_factors.get(rep_type, 0.2)
        
        # Sample size effect (larger samples = more precise)
        sample_precision = 1 / (1 + 100 / original_sample)
        
        # Generate replication effect with noise
        noise = self._rng.gauss(0, variation * (1 - sample_precision))
        rep_effect = original_effect * (1 + noise)
        rep_effect = max(0, rep_effect)  # Effect sizes are typically positive
        
        # Determine significance
        # Simplified power calculation
        power = 0.8 * (1 + (original_sample - 30) / 100)
        if rep_type == ReplicationType.DIRECT:
            power *= 1.1
        
        significant = rep_effect > 0.2 and self._rng.random() < power
        
        # Generate differences
        if rep_type != ReplicationType.DIRECT:
            differences.append("Different sample population")
        
        if self._rng.random() < 0.3:
            differences.append("Different measurement timing")
        
        if self._rng.random() < 0.2:
            differences.append("Different experimental setting")
        
        if rep_type == ReplicationType.CONCEPTUAL:
            differences.append("Modified operational definitions")
        
        return rep_effect, significant, differences
    
    def _calculate_similarity_score(
        self,
        original_effect: float,
        rep_effect: float,
        differences: List[str],
    ) -> float:
        """Calculate similarity between original and replication."""
        # Effect size similarity
        if original_effect == 0:
            effect_similarity = 1.0 if rep_effect == 0 else 0.5
        else:
            ratio = rep_effect / original_effect
            effect_similarity = max(0, 1 - abs(1 - ratio))
        
        # Methodological similarity
        method_similarity = max(0, 1 - len(differences) * 0.15)
        
        # Combined score
        similarity = effect_similarity * 0.7 + method_similarity * 0.3
        
        return round(min(max(similarity, 0.0), 1.0), 3)
    
    def _assess_confidence(
        self,
        concordance: bool,
        similarity: float,
        rep_type: ReplicationType,
        effect_ratio: float,
    ) -> float:
        """Assess confidence in original finding based on replication."""
        base_confidence = 0.5
        
        # Concordance boost
        if concordance:
            base_confidence += 0.3
        
        # Similarity boost
        base_confidence += similarity * 0.1
        
        # Replication type factor
        type_factors = {
            ReplicationType.DIRECT: 0.1,
            ReplicationType.CLOSE: 0.05,
            ReplicationType.CONCEPTUAL: 0.0,
            ReplicationType.PARTIAL: 0.02,
        }
        base_confidence += type_factors.get(rep_type, 0)
        
        # Effect size consistency
        if 0.7 < effect_ratio < 1.3:
            base_confidence += 0.05
        
        return round(min(max(base_confidence, 0.1), 0.95), 3)
    
    def _generate_recommendation(
        self,
        concordance: bool,
        similarity: float,
        rep_type: ReplicationType,
        confidence: float,
    ) -> str:
        """Generate recommendation based on replication results."""
        if concordance and similarity > 0.7:
            return (
                f"Strong replication support. Original finding appears reliable. "
                f"Confidence: {confidence:.1%}"
            )
        elif concordance:
            return (
                f"Moderate replication support with some methodological variations. "
                f"Original finding appears reasonably reliable."
            )
        elif similarity > 0.5:
            return (
                f"Partial replication. Effect size reduced but direction consistent. "
                f"Consider the finding with appropriate caveats."
            )
        else:
            return (
                f"Replication failed to confirm original finding. "
                f"Consider methodological differences and potential publication bias."
            )
