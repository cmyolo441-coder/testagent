"""Discovery Claim Validator - Validates scientific discovery claims."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class ValidationLevel(Enum):
    """Levels of validation."""
    PRELIMINARY = "preliminary"
    BASIC = "basic"
    RIGOROUS = "rigorous"
    COMPREHENSIVE = "comprehensive"
    DEFINITIVE = "definitive"


@dataclass
class ValidationResult:
    """Result of validation."""
    claim: str
    validation_level: ValidationLevel
    is_valid: bool
    confidence: float
    evidence_quality: float
    methodology_quality: float
    reproducibility_score: float
    issues: List[str]
    recommendations: List[str]
    validation_steps_completed: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "validation_level": self.validation_level.value,
            "is_valid": self.is_valid,
            "confidence": self.confidence,
            "evidence_quality": self.evidence_quality,
            "methodology_quality": self.methodology_quality,
            "reproducibility_score": self.reproducibility_score,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "validation_steps_completed": self.validation_steps_completed,
        }


class DiscoveryClaimValidator:
    """Validates scientific discovery claims.
    
    Implements multi-level validation of scientific discoveries
    to assess their credibility and reliability.
    """
    
    def __init__(self):
        self._validations: Dict[str, ValidationResult] = {}
    
    def validate(
        self, claim: Dict[str, Any], validation_level: ValidationLevel = ValidationLevel.BASIC
    ) -> ValidationResult:
        """Validate a discovery claim.
        
        Args:
            claim: Discovery claim dictionary
            validation_level: Level of validation to perform
            
        Returns:
            ValidationResult with validation assessment
        """
        claim_text = claim.get("statement", "")
        evidence = claim.get("evidence", [])
        methodology = claim.get("methodology", {})
        sample_size = claim.get("sample_size", 0)
        
        # Perform validation steps
        steps_completed = []
        issues = []
        
        # Step 1: Check for sufficient evidence
        if len(evidence) >= 3:
            steps_completed.append("Evidence sufficiency check - PASSED")
        else:
            steps_completed.append("Evidence sufficiency check - FAILED")
            issues.append("Insufficient evidence provided")
        
        # Step 2: Check methodology
        if methodology.get("design"):
            steps_completed.append("Methodology review - PASSED")
        else:
            steps_completed.append("Methodology review - INCOMPLETE")
            issues.append("Methodology details incomplete")
        
        # Step 3: Sample size check
        if sample_size >= 30:
            steps_completed.append("Sample size adequacy - PASSED")
        else:
            steps_completed.append("Sample size adequacy - NEEDS IMPROVEMENT")
            issues.append(f"Sample size ({sample_size}) may be insufficient")
        
        # Step 4: Check for extraordinary claims
        if self._is_extraordinary_claim(claim_text):
            steps_completed.append("Extraordinary claims assessment - FLAGGED")
            issues.append("Extraordinary claims require extraordinary evidence")
        
        # Calculate scores
        evidence_quality = self._assess_evidence_quality(evidence)
        methodology_quality = self._assess_methodology_quality(methodology)
        reproducibility = self._assess_reproducibility(claim, methodology)
        
        # Overall confidence
        confidence = self._calculate_confidence(
            evidence_quality, methodology_quality, reproducibility, sample_size
        )
        
        # Determine validity
        is_valid = confidence > 0.6 and len(issues) < 3
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues, validation_level)
        
        result = ValidationResult(
            claim=claim_text,
            validation_level=validation_level,
            is_valid=is_valid,
            confidence=confidence,
            evidence_quality=evidence_quality,
            methodology_quality=methodology_quality,
            reproducibility_score=reproducibility,
            issues=issues,
            recommendations=recommendations,
            validation_steps_completed=steps_completed,
        )
        
        self._validations[claim_text[:50]] = result
        return result
    
    def _is_extraordinary_claim(self, claim: str) -> bool:
        """Check if claim is extraordinary."""
        extraordinary_keywords = [
            "revolutionary", "paradigm shift", "breakthrough",
            "contradicts", "impossible", "never before",
            "cure", "perpetual", "infinite",
        ]
        
        return any(kw in claim.lower() for kw in extraordinary_keywords)
    
    def _assess_evidence_quality(self, evidence: List[Any]) -> float:
        """Assess quality of evidence."""
        if not evidence:
            return 0.0
        
        score = 0.5
        
        # More evidence is better (up to a point)
        if len(evidence) >= 5:
            score += 0.2
        elif len(evidence) >= 3:
            score += 0.1
        
        # Check for diverse evidence types
        evidence_types = set()
        for ev in evidence:
            if isinstance(ev, dict):
                evidence_types.add(ev.get("type", "unknown"))
        
        if len(evidence_types) >= 3:
            score += 0.2
        
        return min(score, 1.0)
    
    def _assess_methodology_quality(self, methodology: Dict[str, Any]) -> float:
        """Assess methodology quality."""
        score = 0.3
        
        if methodology.get("design"):
            score += 0.2
        if methodology.get("controls"):
            score += 0.2
        if methodology.get("analysis_plan"):
            score += 0.2
        if methodology.get("blinding"):
            score += 0.1
        
        return min(score, 1.0)
    
    def _assess_reproducibility(
        self, claim: Dict[str, Any], methodology: Dict[str, Any]
    ) -> float:
        """Assess reproducibility potential."""
        score = 0.5
        
        # Check if methodology is detailed enough
        if methodology.get("detailed_protocol"):
            score += 0.2
        
        # Check if data is available
        if claim.get("data_available"):
            score += 0.2
        
        # Check for replication attempts
        if claim.get("replications", 0) > 0:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_confidence(
        self,
        evidence_quality: float,
        methodology_quality: float,
        reproducibility: float,
        sample_size: int,
    ) -> float:
        """Calculate overall confidence."""
        base_confidence = (
            evidence_quality * 0.35
            + methodology_quality * 0.35
            + reproducibility * 0.30
        )
        
        # Sample size adjustment
        if sample_size >= 100:
            base_confidence += 0.1
        elif sample_size >= 50:
            base_confidence += 0.05
        
        return min(max(base_confidence, 0.0), 1.0)
    
    def _generate_recommendations(
        self, issues: List[str], level: ValidationLevel
    ) -> List[str]:
        """Generate validation recommendations."""
        recommendations = []
        
        if any("evidence" in i.lower() for i in issues):
            recommendations.append("Collect additional supporting evidence")
        
        if any("methodology" in i.lower() for i in issues):
            recommendations.append("Strengthen experimental methodology")
        
        if any("sample" in i.lower() for i in issues):
            recommendations.append("Increase sample size for greater statistical power")
        
        if level in [ValidationLevel.RIGOROUS, ValidationLevel.COMPREHENSIVE]:
            recommendations.append("Conduct independent replication study")
        
        if not recommendations:
            recommendations.append("Continue monitoring and validation")
        
        return recommendations[:4]
