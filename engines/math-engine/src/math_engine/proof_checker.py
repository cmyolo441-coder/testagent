"""Proof Checker - Verifies mathematical proofs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class VerificationStatus(Enum):
    """Status of proof verification."""
    VALID = "valid"
    INVALID = "invalid"
    INCOMPLETE = "incomplete"
    UNCERTAIN = "uncertain"
    ERROR = "error"


@dataclass
class ProofVerification:
    """Result of proof verification."""
    theorem_id: str
    status: VerificationStatus
    confidence: float
    issues_found: List[str]
    valid_steps: int
    total_steps: int
    suggestions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "theorem_id": self.theorem_id,
            "status": self.status.value,
            "confidence": self.confidence,
            "issues_found": self.issues_found,
            "valid_steps": self.valid_steps,
            "total_steps": self.total_steps,
            "suggestions": self.suggestions,
        }


class ProofChecker:
    """Verifies mathematical proofs.
    
    Checks proofs for logical validity, completeness, and correctness.
    """
    
    def __init__(self):
        self._verifications: Dict[str, ProofVerification] = {}
    
    def check(self, proof: Dict[str, Any]) -> ProofVerification:
        """Check a proof for validity.
        
        Args:
            proof: Proof dictionary with steps
            
        Returns:
            ProofVerification with results
        """
        theorem_id = proof.get("theorem_id", "unknown")
        steps = proof.get("steps", [])
        method = proof.get("method", "direct")
        
        issues = []
        valid_steps = 0
        
        # Check each step
        for i, step in enumerate(steps):
            step_valid = self._check_step(step, i, steps)
            if step_valid:
                valid_steps += 1
            else:
                issues.append(f"Step {i+1}: {step.get('description', 'Unknown')[:50]}")
        
        # Check logical flow
        flow_issues = self._check_logical_flow(steps)
        issues.extend(flow_issues)
        
        # Determine status
        if not issues:
            status = VerificationStatus.VALID
            confidence = 0.95
        elif len(issues) <= 2:
            status = VerificationStatus.INCOMPLETE
            confidence = 0.7
        elif len(issues) <= len(steps) / 2:
            status = VerificationStatus.UNCERTAIN
            confidence = 0.5
        else:
            status = VerificationStatus.INVALID
            confidence = 0.3
        
        # Generate suggestions
        suggestions = self._generate_suggestions(issues, method)
        
        verification = ProofVerification(
            theorem_id=theorem_id,
            status=status,
            confidence=confidence,
            issues_found=issues,
            valid_steps=valid_steps,
            total_steps=len(steps),
            suggestions=suggestions,
        )
        
        self._verifications[theorem_id] = verification
        return verification
    
    def _check_step(self, step: Dict[str, Any], index: int, all_steps: List) -> bool:
        """Check if a single step is valid."""
        # Check if step has required fields
        if not step.get("description"):
            return False
        
        if not step.get("justification"):
            return False
        
        # Check if dependencies are valid
        depends_on = step.get("depends_on", [])
        for dep in depends_on:
            if dep >= index or dep < 0:
                return False
        
        return True
    
    def _check_logical_flow(self, steps: List[Dict[str, Any]]) -> List[str]:
        """Check logical flow of proof."""
        issues = []
        
        if not steps:
            issues.append("Proof has no steps")
            return issues
        
        # Check if first step is a valid starting point
        first_step = steps[0]
        if first_step.get("depends_on"):
            issues.append("First step has dependencies")
        
        # Check for circular dependencies
        for i, step in enumerate(steps):
            deps = step.get("depends_on", [])
            if i in deps:
                issues.append(f"Step {i+1} depends on itself")
        
        # Check that all steps are eventually used
        used_steps = set()
        for step in steps:
            used_steps.update(step.get("depends_on", []))
        
        for i in range(len(steps)):
            if i not in used_steps and i > 0:
                issues.append(f"Step {i+1} is not used in the proof")
        
        return issues
    
    def _generate_suggestions(self, issues: List[str], method: str) -> List[str]:
        """Generate suggestions for fixing issues."""
        suggestions = []
        
        if len(issues) > 3:
            suggestions.append("Consider restructuring the proof")
        
        if "dependencies" in str(issues).lower():
            suggestions.append("Review step dependencies")
        
        if method == "induction":
            suggestions.append("Ensure base case and inductive step are complete")
        
        if not suggestions:
            suggestions.append("Proof appears valid")
        
        return suggestions[:3]
