"""Hypothesis Generator - Generates scientific hypotheses from observations and context."""

from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


class HypothesisType(Enum):
    """Types of scientific hypotheses."""
    CAUSAL = "causal"
    CORRELATIONAL = "correlational"
    EXPLANATORY = "explanatory"
    PREDICTIVE = "predictive"
    DESCRIPTIVE = "descriptive"
    COMPARATIVE = "comparative"
    STRUCTURAL = "structural"


@dataclass
class Hypothesis:
    """Represents a scientific hypothesis."""
    id: str
    statement: str
    hypothesis_type: HypothesisType
    confidence: float
    variables: List[str]
    assumptions: List[str]
    testable_predictions: List[str]
    background_theory: str
    created_at: datetime = field(default_factory=datetime.now)
    falsifiability_score: float = 0.0
    novelty_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "type": self.hypothesis_type.value,
            "confidence": self.confidence,
            "variables": self.variables,
            "assumptions": self.assumptions,
            "testable_predictions": self.testable_predictions,
            "background_theory": self.background_theory,
            "created_at": self.created_at.isoformat(),
            "falsifiability_score": self.falsifiability_score,
            "novelty_score": self.novelty_score,
        }


class HypothesisGenerator:
    """Generates scientific hypotheses from observations and context.
    
    Uses pattern recognition, causal inference, and analogical reasoning
    to propose testable hypotheses.
    """
    
    # Templates for different hypothesis types
    CAUSAL_TEMPLATES = [
        "{cause} leads to {effect} in {context}",
        "Changes in {variable_x} cause changes in {variable_y}",
        "{factor} is a determining factor for {outcome}",
        "The relationship between {x} and {y} is mediated by {mediator}",
    ]
    
    CORRELATIONAL_TEMPLATES = [
        "{variable_x} is positively correlated with {variable_y}",
        "There exists an association between {x} and {y}",
        "{factor_a} and {factor_b} co-vary systematically",
    ]
    
    EXPLANATORY_TEMPLATES = [
        "The observed {phenomenon} can be explained by {mechanism}",
        "{theory} provides a mechanism for {observation}",
        "The underlying cause of {effect} is {mechanism}",
    ]
    
    PREDICTIVE_TEMPLATES = [
        "Given {condition}, we predict {outcome}",
        "{variable_x} will predict {variable_y} in future observations",
        "When {condition} is met, {outcome} will occur",
    ]

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._hypothesis_counter = 0
        self._domain_knowledge: Dict[str, List[str]] = {}
    
    def generate(
        self,
        observations: List[str],
        context: Dict[str, Any],
        max_hypotheses: int = 5
    ) -> List[Hypothesis]:
        """Generate hypotheses from observations and context.
        
        Args:
            observations: List of observed phenomena or data points
            context: Additional context including domain, prior knowledge, etc.
            max_hypotheses: Maximum number of hypotheses to generate
            
        Returns:
            List of generated hypotheses with confidence scores
        """
        if not observations:
            return []
        
        domain = context.get("domain", "general")
        prior_knowledge = context.get("prior_knowledge", [])
        variables = context.get("variables", [])
        
        extracted_variables = self._extract_variables(observations, variables)
        patterns = self._detect_patterns(observations, extracted_variables)
        
        hypotheses: List[Hypothesis] = []
        
        # Generate causal hypotheses
        causal_hyps = self._generate_causal_hypotheses(
            observations, extracted_variables, patterns, domain, prior_knowledge
        )
        hypotheses.extend(causal_hyps)
        
        # Generate correlational hypotheses
        correl_hyps = self._generate_correlational_hypotheses(
            observations, extracted_variables, patterns, domain
        )
        hypotheses.extend(correl_hyps)
        
        # Generate explanatory hypotheses
        explan_hyps = self._generate_explanatory_hypotheses(
            observations, extracted_variables, patterns, domain, prior_knowledge
        )
        hypotheses.extend(explan_hyps)
        
        # Generate predictive hypotheses
        predict_hyps = self._generate_predictive_hypotheses(
            observations, extracted_variables, patterns, context
        )
        hypotheses.extend(predict_hyps)
        
        # Rank and filter hypotheses
        ranked = self._rank_hypotheses(hypotheses, observations, context)
        
        return ranked[:max_hypotheses]
    
    def _extract_variables(
        self, observations: List[str], explicit_variables: List[str]
    ) -> List[str]:
        """Extract variables from observations and explicit list."""
        variables = set(explicit_variables)
        
        # Common variable patterns
        variable_patterns = [
            r"(?:the |a |an )?(\w+(?:\s+\w+)?)\s+(?:increases?|decreases?|changes?|affects?|influences?)",
            r"(\w+)\s+(?:and|with|vs\.?|versus)\s+(\w+)",
            r"(?:relationship|correlation|association)\s+between\s+(\w+)\s+and\s+(\w+)",
        ]
        
        for obs in observations:
            for pattern in variable_patterns:
                matches = re.findall(pattern, obs, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        variables.update(match)
                    else:
                        variables.add(match)
        
        return list(variables)
    
    def _detect_patterns(
        self, observations: List[str], variables: List[str]
    ) -> Dict[str, Any]:
        """Detect patterns in observations."""
        patterns = {
            "temporal_sequences": [],
            "correlations": [],
            "causal_language": [],
            "anomalies": [],
            "similarities": [],
        }
        
        temporal_keywords = ["before", "after", "during", "then", "followed by", "preceded"]
        causal_keywords = ["causes", "leads to", "results in", "because", "due to", "effect"]
        anomaly_keywords = ["unexpected", "surprising", "anomaly", "outlier", "deviation"]
        
        for obs in observations:
            obs_lower = obs.lower()
            
            for kw in temporal_keywords:
                if kw in obs_lower:
                    patterns["temporal_sequences"].append(obs)
                    break
            
            for kw in causal_keywords:
                if kw in obs_lower:
                    patterns["causal_language"].append(obs)
                    break
            
            for kw in anomaly_keywords:
                if kw in obs_lower:
                    patterns["anomalies"].append(obs)
                    break
        
        # Detect potential correlations
        if len(variables) >= 2:
            for i, v1 in enumerate(variables):
                for v2 in variables[i+1:]:
                    for obs in observations:
                        if v1.lower() in obs.lower() and v2.lower() in obs.lower():
                            patterns["correlations"].append((v1, v2, obs))
                            break
        
        return patterns
    
    def _generate_causal_hypotheses(
        self,
        observations: List[str],
        variables: List[str],
        patterns: Dict[str, Any],
        domain: str,
        prior_knowledge: List[str],
    ) -> List[Hypothesis]:
        """Generate causal hypotheses."""
        hypotheses = []
        
        causal_obs = patterns.get("causal_language", [])
        if not causal_obs and len(variables) >= 2:
            causal_obs = observations[:2]
        
        for i, obs in enumerate(causal_obs[:3]):
            if len(variables) >= 2:
                cause = variables[i % len(variables)]
                effect = variables[(i + 1) % len(variables)]
            else:
                cause = f"Factor_{i}"
                effect = f"Outcome_{i}"
            
            template = self._rng.choice(self.CAUSAL_TEMPLATES)
            statement = template.format(
                cause=cause,
                effect=effect,
                context=domain,
                variable_x=cause,
                variable_y=effect,
                factor=cause,
                outcome=effect,
                x=cause,
                y=effect,
                mediator=f"Mediator_{i}",
            )
            
            confidence = self._compute_confidence(
                statement, observations, prior_knowledge
            )
            
            hyp = Hypothesis(
                id=self._generate_id(statement),
                statement=statement,
                hypothesis_type=HypothesisType.CAUSAL,
                confidence=confidence,
                variables=[cause, effect],
                assumptions=[
                    f"No confounding variables affect {cause} and {effect}",
                    f"The relationship is not spurious",
                ],
                testable_predictions=[
                    f"Manipulating {cause} will change {effect}",
                    f"Controlling for confounders will preserve the relationship",
                ],
                background_theory=f"Based on observed patterns in {domain}",
                falsifiability_score=self._compute_falsifiability(statement),
                novelty_score=self._compute_novelty(statement, prior_knowledge),
            )
            hypotheses.append(hyp)
        
        return hypotheses
    
    def _generate_correlational_hypotheses(
        self,
        observations: List[str],
        variables: List[str],
        patterns: Dict[str, Any],
        domain: str,
    ) -> List[Hypothesis]:
        """Generate correlational hypotheses."""
        hypotheses = []
        correlations = patterns.get("correlations", [])
        
        for i, (v1, v2, obs) in enumerate(correlations[:3]):
            template = self._rng.choice(self.CORRELATIONAL_TEMPLATES)
            direction = self._rng.choice(["positively", "negatively"])
            
            statement = template.format(
                variable_x=v1,
                variable_y=v2,
                x=v1,
                y=v2,
                factor_a=v1,
                factor_b=v2,
            )
            statement = statement.replace("correlated", f"{direction} correlated")
            
            confidence = 0.5 + self._rng.uniform(-0.1, 0.2)
            
            hyp = Hypothesis(
                id=self._generate_id(statement),
                statement=statement,
                hypothesis_type=HypothesisType.CORRELATIONAL,
                confidence=min(max(confidence, 0.1), 0.95),
                variables=[v1, v2],
                assumptions=[f"Both variables are measurable", f"Correlation is consistent"],
                testable_predictions=[
                    f"Statistical tests will show significant correlation between {v1} and {v2}",
                ],
                background_theory=f"Observed association in {domain} data",
                falsifiability_score=0.7,
                novelty_score=0.4,
            )
            hypotheses.append(hyp)
        
        return hypotheses
    
    def _generate_explanatory_hypotheses(
        self,
        observations: List[str],
        variables: List[str],
        patterns: Dict[str, Any],
        domain: str,
        prior_knowledge: List[str],
    ) -> List[Hypothesis]:
        """Generate explanatory hypotheses."""
        hypotheses = []
        anomalies = patterns.get("anomalies", [])
        
        for i, obs in enumerate(anomalies[:2]):
            template = self._rng.choice(self.EXPLANATORY_TEMPLATES)
            
            mechanisms = [
                "a previously unidentified mechanism",
                "emergent properties of the system",
                "nonlinear interactions between components",
                "boundary conditions not previously considered",
            ]
            
            statement = template.format(
                phenomenon=obs[:50] if len(obs) > 50 else obs,
                observation=obs[:50],
                mechanism=self._rng.choice(mechanisms),
                theory=f"Current {domain} theory",
                effect=obs[:50],
            )
            
            confidence = 0.4 + self._rng.uniform(0, 0.3)
            
            hyp = Hypothesis(
                id=self._generate_id(statement),
                statement=statement,
                hypothesis_type=HypothesisType.EXPLANATORY,
                confidence=min(confidence, 0.85),
                variables=variables[:3] if variables else ["Mechanism"],
                assumptions=[
                    "Existing theories are incomplete",
                    "The mechanism is discoverable",
                ],
                testable_predictions=[
                    "The proposed mechanism will be observable under controlled conditions",
                    "Predictions from the explanation will match new observations",
                ],
                background_theory=f"Extension of {domain} theory",
                falsifiability_score=0.8,
                novelty_score=0.7,
            )
            hypotheses.append(hyp)
        
        return hypotheses
    
    def _generate_predictive_hypotheses(
        self,
        observations: List[str],
        variables: List[str],
        patterns: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[Hypothesis]:
        """Generate predictive hypotheses."""
        hypotheses = []
        
        temporal = patterns.get("temporal_sequences", [])
        
        if len(variables) >= 2 or temporal:
            for i in range(min(2, max(1, len(observations) // 2))):
                if len(variables) >= 2:
                    predictor = variables[i % len(variables)]
                    outcome = variables[(i + 1) % len(variables)]
                else:
                    predictor = f"Predictor_{i}"
                    outcome = f"Outcome_{i}"
                
                template = self._rng.choice(self.PREDICTIVE_TEMPLATES)
                statement = template.format(
                    condition=f"high {predictor}" if self._rng.random() > 0.5 else f"changes in {predictor}",
                    outcome=outcome,
                    variable_x=predictor,
                    variable_y=outcome,
                )
                
                confidence = 0.45 + self._rng.uniform(0, 0.25)
                
                hyp = Hypothesis(
                    id=self._generate_id(statement),
                    statement=statement,
                    hypothesis_type=HypothesisType.PREDICTIVE,
                    confidence=min(confidence, 0.9),
                    variables=[predictor, outcome],
                    assumptions=[
                        "Historical patterns will continue",
                        "No structural breaks in the system",
                    ],
                    testable_predictions=[
                        f"Future observations will confirm {predictor} predicts {outcome}",
                    ],
                    background_theory="Extrapolation from observed temporal patterns",
                    falsifiability_score=0.75,
                    novelty_score=0.5,
                )
                hypotheses.append(hyp)
        
        return hypotheses
    
    def _compute_confidence(
        self,
        statement: str,
        observations: List[str],
        prior_knowledge: List[str],
    ) -> float:
        """Compute confidence score for a hypothesis."""
        base_confidence = 0.5
        
        # Boost for matching prior knowledge
        for knowledge in prior_knowledge:
            if any(word in knowledge.lower() for word in statement.lower().split()):
                base_confidence += 0.05
        
        # Boost for multiple supporting observations
        supporting = sum(1 for obs in observations 
                        if any(w in obs.lower() for w in statement.lower().split() if len(w) > 3))
        base_confidence += min(supporting * 0.05, 0.2)
        
        # Add noise
        base_confidence += self._rng.uniform(-0.05, 0.1)
        
        return min(max(base_confidence, 0.1), 0.95)
    
    def _compute_falsifiability(self, statement: str) -> float:
        """Compute falsifiability score."""
        score = 0.5
        
        # More specific statements are more falsifiable
        if any(c.isdigit() for c in statement):
            score += 0.1
        if any(kw in statement.lower() for kw in ["always", "never", "all", "none"]):
            score += 0.15
        if any(kw in statement.lower() for kw in ["increase", "decrease", "correlat"]):
            score += 0.1
        
        return min(score, 1.0)
    
    def _compute_novelty(self, statement: str, prior_knowledge: List[str]) -> float:
        """Compute novelty score."""
        novelty = 0.7
        
        for knowledge in prior_knowledge:
            overlap = len(set(statement.lower().split()) & set(knowledge.lower().split()))
            if overlap > 3:
                novelty -= 0.1
        
        return max(novelty, 0.1)
    
    def _generate_id(self, statement: str) -> str:
        """Generate unique ID for a hypothesis."""
        self._hypothesis_counter += 1
        hash_input = f"{statement}{self._hypothesis_counter}"
        hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"HYP-{hash_val.upper()}"
    
    def _rank_hypotheses(
        self,
        hypotheses: List[Hypothesis],
        observations: List[str],
        context: Dict[str, Any],
    ) -> List[Hypothesis]:
        """Rank hypotheses by composite score."""
        def composite_score(h: Hypothesis) -> float:
            return (
                h.confidence * 0.4
                + h.falsifiability_score * 0.3
                + h.novelty_score * 0.3
            )
        
        return sorted(hypotheses, key=composite_score, reverse=True)
