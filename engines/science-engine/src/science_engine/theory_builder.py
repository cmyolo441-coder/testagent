"""Theory Builder - Constructs scientific theories from hypotheses and evidence."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime


class TheoryStatus(Enum):
    """Status of a scientific theory."""
    PROPOSED = "proposed"
    TESTING = "testing"
    SUPPORTED = "supported"
    REFINED = "refined"
    DISPUTED = "disputed"
    FALSIFIED = "falsified"
    ACCEPTED = "accepted"


class EvidenceStrength(Enum):
    """Strength of evidence."""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    ANECDOTAL = "anecdotal"
    CONFLICTING = "conflicting"


@dataclass
class Evidence:
    """Represents a piece of evidence."""
    id: str
    description: str
    source: str
    strength: EvidenceStrength
    supports_hypothesis: bool
    confidence: float
    methodology: str
    sample_size: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "source": self.source,
            "strength": self.strength.value,
            "supports_hypothesis": self.supports_hypothesis,
            "confidence": self.confidence,
            "methodology": self.methodology,
            "sample_size": self.sample_size,
        }


@dataclass
class Theory:
    """Represents a scientific theory."""
    id: str
    name: str
    description: str
    status: TheoryStatus
    hypotheses: List[str]  # Hypothesis IDs
    supporting_evidence: List[Evidence]
    contradicting_evidence: List[Evidence]
    predictions: List[str]
    assumptions: List[str]
    scope: str
    mathematical_formulation: Optional[str]
    explanatory_power: float
    predictive_power: float
    parsimony: float
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "hypotheses": self.hypotheses,
            "supporting_evidence": [e.to_dict() for e in self.supporting_evidence],
            "contradicting_evidence": [e.to_dict() for e in self.contradicting_evidence],
            "predictions": self.predictions,
            "assumptions": self.assumptions,
            "scope": self.scope,
            "mathematical_formulation": self.mathematical_formulation,
            "explanatory_power": self.explanatory_power,
            "predictive_power": self.predictive_power,
            "parsimony": self.parsimony,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class TheoryBuilder:
    """Constructs scientific theories from hypotheses and evidence.
    
    Integrates multiple hypotheses and pieces of evidence into coherent
    theoretical frameworks, evaluating their strength and coherence.
    """
    
    def __init__(self):
        self._theories: Dict[str, Theory] = {}
        self._theory_counter = 0
    
    def build(
        self,
        hypotheses: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]],
        domain: str = "general"
    ) -> Theory:
        """Build a theory from hypotheses and evidence.
        
        Args:
            hypotheses: List of hypothesis dictionaries
            evidence: List of evidence dictionaries
            domain: Scientific domain
            
        Returns:
            Constructed Theory object
        """
        self._theory_counter += 1
        
        # Parse hypotheses and evidence
        hypothesis_ids = [h.get("id", f"HYP-{i}") for i, h in enumerate(hypotheses)]
        supporting_evidence = self._filter_evidence(evidence, supports=True)
        contradicting_evidence = self._filter_evidence(evidence, supports=False)
        
        # Generate theory name and description
        name = self._generate_theory_name(hypotheses, domain)
        description = self._generate_theory_description(hypotheses, evidence, domain)
        
        # Generate predictions from hypotheses
        predictions = self._extract_predictions(hypotheses)
        
        # Extract assumptions
        assumptions = self._extract_assumptions(hypotheses)
        
        # Determine scope
        scope = self._determine_scope(hypotheses, domain)
        
        # Calculate theory metrics
        explanatory_power = self._calculate_explanatory_power(hypotheses, evidence)
        predictive_power = self._calculate_predictive_power(hypotheses)
        parsimony = self._calculate_parsimony(hypotheses, assumptions)
        
        # Determine status
        status = self._determine_status(supporting_evidence, contradicting_evidence)
        
        # Generate mathematical formulation if applicable
        math_formulation = self._generate_mathematical_formulation(hypotheses, domain)
        
        theory_id = f"THY-{hashlib.md5(f'{name}{self._theory_counter}'.encode()).hexdigest()[:8].upper()}"
        
        theory = Theory(
            id=theory_id,
            name=name,
            description=description,
            status=status,
            hypotheses=hypothesis_ids,
            supporting_evidence=supporting_evidence,
            contradicting_evidence=contradicting_evidence,
            predictions=predictions,
            assumptions=assumptions,
            scope=scope,
            mathematical_formulation=math_formulation,
            explanatory_power=explanatory_power,
            predictive_power=predictive_power,
            parsimony=parsimony,
        )
        
        self._theories[theory_id] = theory
        return theory
    
    def _filter_evidence(
        self, evidence: List[Dict[str, Any]], supports: bool
    ) -> List[Evidence]:
        """Filter evidence by whether it supports or contradicts hypotheses."""
        filtered = []
        for e in evidence:
            e_supports = e.get("supports_hypothesis", True)
            if e_supports == supports:
                strength_str = e.get("strength", "moderate")
                try:
                    strength = EvidenceStrength(strength_str)
                except ValueError:
                    strength = EvidenceStrength.MODERATE
                
                evidence_obj = Evidence(
                    id=e.get("id", f"EV-{len(filtered)}"),
                    description=e.get("description", "No description"),
                    source=e.get("source", "Unknown"),
                    strength=strength,
                    supports_hypothesis=e_supports,
                    confidence=e.get("confidence", 0.5),
                    methodology=e.get("methodology", "Not specified"),
                    sample_size=e.get("sample_size"),
                )
                filtered.append(evidence_obj)
        return filtered
    
    def _generate_theory_name(
        self, hypotheses: List[Dict[str, Any]], domain: str
    ) -> str:
        """Generate a descriptive name for the theory."""
        key_concepts = set()
        for hyp in hypotheses:
            variables = hyp.get("variables", [])
            key_concepts.update(variables[:2])
        
        if key_concepts:
            concepts_str = " and ".join(list(key_concepts)[:3])
            return f"The {concepts_str} Theory of {domain.title()}"
        
        return f"Integrated Theory of {domain.title()}"
    
    def _generate_theory_description(
        self,
        hypotheses: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]],
        domain: str,
    ) -> str:
        """Generate theory description."""
        hyp_count = len(hypotheses)
        ev_count = len(evidence)
        supporting = sum(1 for e in evidence if e.get("supports_hypothesis", True))
        
        description = (
            f"This theory integrates {hyp_count} hypotheses about {domain} "
            f"supported by {supporting} pieces of supporting evidence out of "
            f"{ev_count} total evidence examined. "
        )
        
        # Add key relationships
        relationships = []
        for hyp in hypotheses:
            hyp_type = hyp.get("type", "correlational")
            if hyp_type == "causal":
                relationships.append("causal mechanisms")
            elif hyp_type == "predictive":
                relationships.append("predictive patterns")
            elif hyp_type == "explanatory":
                relationships.append("explanatory frameworks")
        
        if relationships:
            unique_rels = list(dict.fromkeys(relationships))
            description += f"The theory proposes {', '.join(unique_rels)} as fundamental to understanding {domain}."
        
        return description
    
    def _extract_predictions(self, hypotheses: List[Dict[str, Any]]) -> List[str]:
        """Extract testable predictions from hypotheses."""
        predictions = []
        for hyp in hypotheses:
            hyp_predictions = hyp.get("testable_predictions", [])
            predictions.extend(hyp_predictions)
        
        # Add theory-level predictions
        predictions.append("The theory will remain consistent with new empirical observations")
        predictions.append("Interventions based on the theory will produce predicted effects")
        
        return list(dict.fromkeys(predictions))[:10]
    
    def _extract_assumptions(self, hypotheses: List[Dict[str, Any]]) -> List[str]:
        """Extract assumptions from hypotheses."""
        assumptions = []
        for hyp in hypotheses:
            hyp_assumptions = hyp.get("assumptions", [])
            assumptions.extend(hyp_assumptions)
        
        # Add general scientific assumptions
        assumptions.extend([
            "The observed phenomena are real and not artifacts",
            "Measurement instruments are calibrated and reliable",
            "The sample is representative of the population",
        ])
        
        return list(dict.fromkeys(assumptions))[:8]
    
    def _determine_scope(self, hypotheses: List[Dict[str, Any]], domain: str) -> str:
        """Determine the scope of the theory."""
        all_variables = []
        for hyp in hypotheses:
            all_variables.extend(hyp.get("variables", []))
        
        unique_variables = set(all_variables)
        
        if len(unique_variables) > 10:
            return f"Broad scope covering {len(unique_variables)} variables in {domain}"
        elif len(unique_variables) > 5:
            return f"Moderate scope focusing on key variables in {domain}"
        else:
            return f"Narrow scope targeting specific mechanisms in {domain}"
    
    def _calculate_explanatory_power(
        self,
        hypotheses: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]],
    ) -> float:
        """Calculate explanatory power of the theory."""
        if not hypotheses:
            return 0.0
        
        # Base power from number of hypotheses
        base_power = min(len(hypotheses) * 0.15, 0.5)
        
        # Boost from supporting evidence
        supporting = sum(1 for e in evidence if e.get("supports_hypothesis", True))
        evidence_boost = min(supporting * 0.05, 0.3)
        
        # Boost from hypothesis confidence
        confidences = [h.get("confidence", 0.5) for h in hypotheses]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        confidence_boost = avg_confidence * 0.2
        
        return min(base_power + evidence_boost + confidence_boost, 1.0)
    
    def _calculate_predictive_power(self, hypotheses: List[Dict[str, Any]]) -> float:
        """Calculate predictive power of the theory."""
        predictive_hyps = [
            h for h in hypotheses 
            if h.get("type") == "predictive"
        ]
        
        if not hypotheses:
            return 0.0
        
        # Ratio of predictive hypotheses
        predictive_ratio = len(predictive_hyps) / len(hypotheses)
        
        # Base predictive power
        base_power = predictive_ratio * 0.5
        
        # Add confidence-based boost
        if predictive_hyps:
            avg_conf = sum(h.get("confidence", 0.5) for h in predictive_hyps) / len(predictive_hyps)
            base_power += avg_conf * 0.3
        
        return min(base_power, 1.0)
    
    def _calculate_parsimony(
        self, hypotheses: List[Dict[str, Any]], assumptions: List[str]
    ) -> float:
        """Calculate parsimony (simplicity) of the theory."""
        # Fewer hypotheses = more parsimonious
        hyp_penalty = min(len(hypotheses) * 0.1, 0.5)
        
        # Fewer assumptions = more parsimonious
        assumption_penalty = min(len(assumptions) * 0.05, 0.3)
        
        parsimony = 1.0 - hyp_penalty - assumption_penalty
        return max(parsimony, 0.1)
    
    def _determine_status(
        self,
        supporting: List[Evidence],
        contradicting: List[Evidence],
    ) -> TheoryStatus:
        """Determine theory status based on evidence."""
        total = len(supporting) + len(contradicting)
        
        if total == 0:
            return TheoryStatus.PROPOSED
        
        support_ratio = len(supporting) / total
        
        if support_ratio >= 0.8:
            return TheoryStatus.SUPPORTED
        elif support_ratio >= 0.6:
            return TheoryStatus.TESTING
        elif support_ratio >= 0.4:
            return TheoryStatus.DISPUTED
        else:
            return TheoryStatus.FALSIFIED
    
    def _generate_mathematical_formulation(
        self, hypotheses: List[Dict[str, Any]], domain: str
    ) -> Optional[str]:
        """Generate mathematical formulation if applicable."""
        causal_hyps = [h for h in hypotheses if h.get("type") == "causal"]
        
        if causal_hyps:
            variables = []
            for h in causal_hyps:
                variables.extend(h.get("variables", []))
            
            unique_vars = list(dict.fromkeys(variables))[:5]
            
            # Generate simple mathematical representation
            if len(unique_vars) >= 2:
                var_str = ", ".join(unique_vars[:4])
                return f"F({var_str}) = β₀ + Σβᵢxᵢ + ε, where relationships are {domain}-specific"
        
        return None
