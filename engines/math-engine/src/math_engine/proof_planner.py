"""Proof Planner - Plans proof strategies for theorems."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class ProofMethod(Enum):
    """Proof methods."""
    DIRECT = "direct"
    CONTRAPOSITIVE = "contrapositive"
    CONTRADICTION = "contradiction"
    INDUCTION = "induction"
    CONSTRUCTION = "construction"
    CASE_ANALYSIS = "case_analysis"
    EXHAUSTION = "exhaustion"
    MATHEMATICAL_INDUCTION = "mathematical_induction"
    STRONG_INDUCTION = "strong_induction"


@dataclass
class ProofStep:
    """A step in a proof outline."""
    step_number: int
    description: str
    justification: str
    depends_on: List[int]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "description": self.description,
            "justification": self.justification,
            "depends_on": self.depends_on,
        }


@dataclass
class ProofOutline:
    """Outline of a proof."""
    theorem_id: str
    method: ProofMethod
    steps: List[ProofStep]
    key_lemmas: List[str]
    assumptions: List[str]
    difficulty_estimate: str
    estimated_steps: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "theorem_id": self.theorem_id,
            "method": self.method.value,
            "steps": [s.to_dict() for s in self.steps],
            "key_lemmas": self.key_lemmas,
            "assumptions": self.assumptions,
            "difficulty_estimate": self.difficulty_estimate,
            "estimated_steps": self.estimated_steps,
        }


class ProofPlanner:
    """Plans proof strategies for theorems.
    
    Analyzes theorems and generates proof outlines using
    appropriate proof strategies.
    """
    
    def __init__(self):
        self._plans: Dict[str, ProofOutline] = {}
    
    def plan(self, theorem: Dict[str, Any]) -> ProofOutline:
        """Plan a proof for a theorem.
        
        Args:
            theorem: Theorem to prove
            
        Returns:
            ProofOutline with proof strategy
        """
        statement = theorem.get("statement", "")
        hypotheses = theorem.get("hypotheses", [])
        conclusions = theorem.get("conclusions", [])
        
        # Select proof method
        method = self._select_method(statement, hypotheses, conclusions)
        
        # Generate steps
        steps = self._generate_steps(method, statement, hypotheses, conclusions)
        
        # Identify key lemmas
        lemmas = self._identify_lemmas(statement, hypotheses)
        
        # Estimate difficulty
        difficulty = self._estimate_difficulty(method, len(steps))
        
        outline = ProofOutline(
            theorem_id=theorem.get("id", "unknown"),
            method=method,
            steps=steps,
            key_lemmas=lemmas,
            assumptions=hypotheses,
            difficulty_estimate=difficulty,
            estimated_steps=len(steps),
        )
        
        self._plans[theorem.get("id", "unknown")] = outline
        return outline
    
    def _select_method(
        self, statement: str, hypotheses: List[str], conclusions: List[str]
    ) -> ProofMethod:
        """Select appropriate proof method."""
        statement_lower = statement.lower()
        
        # Check for induction indicators
        if any(kw in statement_lower for kw in ["for all n", "for all natural", "for n ≥"]):
            return ProofMethod.MATHEMATICAL_INDUCTION
        
        # Check for contradiction indicators
        if any(kw in statement_lower for kw in ["no", "there is no", "does not exist"]):
            return ProofMethod.CONTRADICTION
        
        # Check for contrapositive
        if any(kw in statement_lower for kw in ["if", "implies"]):
            return ProofMethod.CONTRAPOSITIVE
        
        # Default to direct proof
        return ProofMethod.DIRECT
    
    def _generate_steps(
        self,
        method: ProofMethod,
        statement: str,
        hypotheses: List[str],
        conclusions: List[str],
    ) -> List[ProofStep]:
        """Generate proof steps based on method."""
        steps = []
        
        if method == ProofMethod.MATHEMATICAL_INDUCTION:
            steps = self._induction_steps(statement, hypotheses)
        elif method == ProofMethod.CONTRADICTION:
            steps = self._contradiction_steps(statement, hypotheses)
        elif method == ProofMethod.DIRECT:
            steps = self._direct_steps(statement, hypotheses, conclusions)
        else:
            steps = self._generic_steps(statement)
        
        return steps
    
    def _induction_steps(self, statement: str, hypotheses: List[str]) -> List[ProofStep]:
        """Generate steps for mathematical induction."""
        return [
            ProofStep(1, "State the proposition P(n) to be proven", "Given", []),
            ProofStep(2, "Base case: Verify P(0) or P(1)", "Direct verification", [1]),
            ProofStep(3, "Inductive hypothesis: Assume P(k) holds for some k", "Assumption", [2]),
            ProofStep(4, "Inductive step: Show P(k+1) follows from P(k)", "Logical deduction", [3]),
            ProofStep(5, "Conclude P(n) holds for all n by induction", "Principle of mathematical induction", [2, 4]),
        ]
    
    def _contradiction_steps(self, statement: str, hypotheses: List[str]) -> List[ProofStep]:
        """Generate steps for proof by contradiction."""
        return [
            ProofStep(1, "Assume the negation of the conclusion", "Assumption for contradiction", []),
            ProofStep(2, "Derive consequences from the assumption", "Logical deduction", [1]),
            ProofStep(3, "Reach a contradiction with known facts", "Analysis", [2]),
            ProofStep(4, "Conclude the original statement must be true", "Contradiction principle", [1, 3]),
        ]
    
    def _direct_steps(
        self, statement: str, hypotheses: List[str], conclusions: List[str]
    ) -> List[ProofStep]:
        """Generate steps for direct proof."""
        steps = [
            ProofStep(1, "State the given hypotheses", "Given", []),
        ]
        
        for i, hyp in enumerate(hypotheses[:3], 2):
            steps.append(ProofStep(i, f"Use hypothesis: {hyp[:50]}", "Given", [1]))
        
        next_step = len(steps) + 1
        steps.append(ProofStep(
            next_step, "Apply logical deductions", "Inference rules", list(range(1, next_step))
        ))
        
        steps.append(ProofStep(
            next_step + 1, "Conclude the desired result", "Logical conclusion", [next_step]
        ))
        
        return steps
    
    def _generic_steps(self, statement: str) -> List[ProofStep]:
        """Generate generic proof steps."""
        return [
            ProofStep(1, "Analyze the statement structure", "Analysis", []),
            ProofStep(2, "Identify applicable definitions and theorems", "Knowledge retrieval", [1]),
            ProofStep(3, "Construct the proof using available tools", "Proof construction", [2]),
            ProofStep(4, "Verify the proof is complete and correct", "Verification", [3]),
        ]
    
    def _identify_lemmas(self, statement: str, hypotheses: List[str]) -> List[str]:
        """Identify key lemmas that might be needed."""
        lemmas = []
        
        statement_lower = statement.lower()
        
        if "sum" in statement_lower or "series" in statement_lower:
            lemmas.append("Convergence of series")
        
        if "product" in statement_lower:
            lemmas.append("Properties of products")
        
        if "limit" in statement_lower:
            lemmas.append("Limit laws")
        
        if "integral" in statement_lower:
            lemmas.append("Integration properties")
        
        return lemmas[:3]
    
    def _estimate_difficulty(self, method: ProofMethod, num_steps: int) -> str:
        """Estimate proof difficulty."""
        if num_steps <= 4:
            return "Easy"
        elif num_steps <= 8:
            return "Moderate"
        elif num_steps <= 15:
            return "Hard"
        else:
            return "Very Hard"
