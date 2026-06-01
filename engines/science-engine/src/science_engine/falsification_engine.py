"""Falsification Engine - Attempts to falsify hypotheses using evidence."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


class FalsificationMethod(Enum):
    """Methods for attempting falsification."""
    EMPIRICAL = "empirical"
    LOGICAL = "logical"
    STATISTICAL = "statistical"
    COMPARATIVE = "comparative"
    PREDICTIVE = "predictive"
    BOUNDARY = "boundary"
    REDUCTIO = "reductio"


class FalsificationOutcome(Enum):
    """Outcome of falsification attempt."""
    FALSIFIED = "falsified"
    NOT_FALSIFIED = "not_falsified"
    INCONCLUSIVE = "inconclusive"
    PARTIALLY_FALSIFIED = "partially_falsified"


@dataclass
class FalsificationResult:
    """Result of a falsification attempt."""
    hypothesis_id: str
    method: FalsificationMethod
    outcome: FalsificationOutcome
    confidence: float
    evidence_for_falsification: List[str]
    evidence_against_falsification: List[str]
    logical_issues: List[str]
    statistical_issues: List[str]
    alternative_explanations: List[str]
    recommendations: List[str]
    severity_assessment: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "method": self.method.value,
            "outcome": self.outcome.value,
            "confidence": self.confidence,
            "evidence_for_falsification": self.evidence_for_falsification,
            "evidence_against_falsification": self.evidence_against_falsification,
            "logical_issues": self.logical_issues,
            "statistical_issues": self.statistical_issues,
            "alternative_explanations": self.alternative_explanations,
            "recommendations": self.recommendations,
            "severity_assessment": self.severity_assessment,
        }


class FalsificationEngine:
    """Attempts to falsify hypotheses using multiple methods.
    
    Implements rigorous falsification testing following Popperian
    principles of scientific methodology.
    """
    
    def __init__(self):
        self._results: Dict[str, List[FalsificationResult]] = {}
    
    def attempt_falsification(
        self,
        hypothesis: Dict[str, Any],
        evidence: List[Dict[str, Any]],
    ) -> FalsificationResult:
        """Attempt to falsify a hypothesis.
        
        Args:
            hypothesis: The hypothesis to test
            evidence: Available evidence
            
        Returns:
            FalsificationResult with analysis
        """
        hyp_id = hypothesis.get("id", "unknown")
        
        # Apply multiple falsification methods
        results = []
        
        # 1. Logical falsification
        logical_result = self._logical_falsification(hypothesis, evidence)
        results.append(logical_result)
        
        # 2. Statistical falsification
        statistical_result = self._statistical_falsification(hypothesis, evidence)
        results.append(statistical_result)
        
        # 3. Empirical falsification
        empirical_result = self._empirical_falsification(hypothesis, evidence)
        results.append(empirical_result)
        
        # 4. Comparative falsification
        comparative_result = self._comparative_falsification(hypothesis, evidence)
        results.append(comparative_result)
        
        # 5. Predictive falsification
        predictive_result = self._predictive_falsification(hypothesis, evidence)
        results.append(predictive_result)
        
        # Combine results
        combined = self._combine_results(hyp_id, results)
        
        if hyp_id not in self._results:
            self._results[hyp_id] = []
        self._results[hyp_id].append(combined)
        
        return combined
    
    def _logical_falsification(
        self, hypothesis: Dict[str, Any], evidence: List[Dict[str, Any]]
    ) -> FalsificationResult:
        """Attempt logical falsification."""
        issues = []
        evidence_for = []
        evidence_against = []
        
        statement = hypothesis.get("statement", "")
        assumptions = hypothesis.get("assumptions", [])
        
        # Check for logical inconsistencies
        if "always" in statement.lower() and "never" in statement.lower():
            issues.append("Statement contains contradictory absolutes")
        
        # Check for unfalsifiable claims
        if any(kw in statement.lower() for kw in ["unobservable", "metaphysical", "supernatural"]):
            issues.append("Hypothesis may be unfalsifiable - contains unobservable elements")
        
        # Check assumptions for contradictions
        for i, a1 in enumerate(assumptions):
            for a2 in assumptions[i+1:]:
                if self._are_contradictory(a1, a2):
                    issues.append(f"Contradictory assumptions: '{a1}' vs '{a2}'")
        
        # Check evidence against hypothesis
        for ev in evidence:
            if not ev.get("supports_hypothesis", True):
                evidence_for.append(ev.get("description", "Contradicting evidence"))
            else:
                evidence_against.append(ev.get("description", "Supporting evidence"))
        
        # Determine outcome
        if issues or len(evidence_for) > len(evidence_against):
            outcome = FalsificationOutcome.FALSIFIED
            confidence = 0.7 + len(issues) * 0.1
        elif not evidence_for:
            outcome = FalsificationOutcome.NOT_FALSIFIED
            confidence = 0.6
        else:
            outcome = FalsificationOutcome.INCONCLUSIVE
            confidence = 0.5
        
        return FalsificationResult(
            hypothesis_id=hypothesis.get("id", ""),
            method=FalsificationMethod.LOGICAL,
            outcome=outcome,
            confidence=min(confidence, 0.95),
            evidence_for_falsification=evidence_for[:5],
            evidence_against_falsification=evidence_against[:5],
            logical_issues=issues,
            statistical_issues=[],
            alternative_explanations=[],
            recommendations=self._generate_logical_recommendations(issues),
            severity_assessment=len(issues) * 0.2,
        )
    
    def _are_contradictory(self, statement1: str, statement2: str) -> bool:
        """Check if two statements are contradictory."""
        s1 = statement1.lower()
        s2 = statement2.lower()
        
        contradictory_pairs = [
            ("always", "never"),
            ("all", "none"),
            ("increase", "decrease"),
            ("positive", "negative"),
            ("cause", "prevent"),
        ]
        
        for word1, word2 in contradictory_pairs:
            if (word1 in s1 and word2 in s2) or (word2 in s1 and word1 in s2):
                # Check if discussing same topic
                s1_words = set(s1.split())
                s2_words = set(s2.split())
                overlap = s1_words & s2_words
                if len(overlap) > 2:
                    return True
        
        return False
    
    def _statistical_falsification(
        self, hypothesis: Dict[str, Any], evidence: List[Dict[str, Any]]
    ) -> FalsificationResult:
        """Attempt statistical falsification."""
        issues = []
        evidence_for = []
        evidence_against = []
        
        # Extract statistical information from evidence
        stats_found = []
        for ev in evidence:
            desc = ev.get("description", "").lower()
            if "p=" in desc or "p-value" in desc or "significant" in desc:
                stats_found.append(ev)
                if ev.get("supports_hypothesis", True):
                    evidence_against.append(ev.get("description", ""))
                else:
                    evidence_for.append(ev.get("description", ""))
        
        # Check for statistical issues
        if not stats_found:
            issues.append("No statistical evidence provided")
        
        # Check for multiple testing problems
        if len(stats_found) > 10:
            issues.append("Potential multiple testing problem - consider correction")
        
        # Check for effect sizes
        has_effect_size = any(
            "effect size" in ev.get("description", "").lower() or
            "cohens" in ev.get("description", "").lower()
            for ev in evidence
        )
        if not has_effect_size:
            issues.append("No effect sizes reported - statistical significance may be misleading")
        
        # Check for confidence intervals
        has_ci = any(
            "confidence interval" in ev.get("description", "").lower() or
            "ci" in ev.get("description", "").lower()
            for ev in evidence
        )
        if not has_ci:
            issues.append("No confidence intervals reported")
        
        # Determine outcome
        if len(evidence_for) > 2:
            outcome = FalsificationOutcome.FALSIFIED
            confidence = 0.75
        elif len(issues) > 2:
            outcome = FalsificationOutcome.PARTIALLY_FALSIFIED
            confidence = 0.6
        else:
            outcome = FalsificationOutcome.NOT_FALSIFIED
            confidence = 0.65
        
        return FalsificationResult(
            hypothesis_id=hypothesis.get("id", ""),
            method=FalsificationMethod.STATISTICAL,
            outcome=outcome,
            confidence=min(confidence, 0.9),
            evidence_for_falsification=evidence_for[:5],
            evidence_against_falsification=evidence_against[:5],
            logical_issues=[],
            statistical_issues=issues,
            alternative_explanations=[],
            recommendations=self._generate_statistical_recommendations(issues),
            severity_assessment=len(issues) * 0.15,
        )
    
    def _empirical_falsification(
        self, hypothesis: Dict[str, Any], evidence: List[Dict[str, Any]]
    ) -> FalsificationResult:
        """Attempt empirical falsification."""
        evidence_for = []
        evidence_against = []
        alternatives = []
        
        # Analyze empirical evidence
        for ev in evidence:
            desc = ev.get("description", "")
            supports = ev.get("supports_hypothesis", True)
            
            if supports:
                evidence_against.append(desc)
            else:
                evidence_for.append(desc)
                
                # Generate alternative explanation
                alt = self._generate_alternative_explanation(desc, hypothesis)
                if alt:
                    alternatives.append(alt)
        
        # Check evidence quality
        weak_evidence = []
        for ev in evidence:
            strength = ev.get("strength", "moderate")
            if strength in ("weak", "anecdotal"):
                weak_evidence.append(ev.get("description", ""))
        
        issues = []
        if weak_evidence:
            issues.append(f"Weak evidence detected: {len(weak_evidence)} pieces")
        
        # Determine outcome
        if len(evidence_for) > len(evidence_against):
            outcome = FalsificationOutcome.FALSIFIED
            confidence = 0.7
        elif len(evidence_for) == len(evidence_against) and len(evidence_for) > 0:
            outcome = FalsificationOutcome.INCONCLUSIVE
            confidence = 0.5
        else:
            outcome = FalsificationOutcome.NOT_FALSIFIED
            confidence = 0.6
        
        return FalsificationResult(
            hypothesis_id=hypothesis.get("id", ""),
            method=FalsificationMethod.EMPIRICAL,
            outcome=outcome,
            confidence=min(confidence, 0.9),
            evidence_for_falsification=evidence_for[:5],
            evidence_against_falsification=evidence_against[:5],
            logical_issues=issues,
            statistical_issues=[],
            alternative_explanations=alternatives[:3],
            recommendations=["Collect more definitive empirical evidence"],
            severity_assessment=0.3 if evidence_for else 0.1,
        )
    
    def _generate_alternative_explanation(
        self, contradicting_evidence: str, hypothesis: Dict[str, Any]
    ) -> Optional[str]:
        """Generate alternative explanation for contradicting evidence."""
        alternatives = [
            "Confounding variable not controlled in the study",
            "Measurement error or instrumentation bias",
            "Sample selection bias",
            "Temporal confounding - causation vs correlation",
            "Publication bias in the cited study",
            "Different operational definition of key constructs",
        ]
        
        # Select based on context
        statement = hypothesis.get("statement", "").lower()
        if "causal" in hypothesis.get("type", ""):
            return "Observed correlation may not imply causation - confounding likely"
        elif "predictive" in hypothesis.get("type", ""):
            return "Prediction failure may be due to changed conditions"
        
        return alternatives[0] if alternatives else None
    
    def _comparative_falsification(
        self, hypothesis: Dict[str, Any], evidence: List[Dict[str, Any]]
    ) -> FalsificationResult:
        """Attempt comparative falsification against existing theories."""
        issues = []
        evidence_for = []
        alternatives = []
        
        # Check if hypothesis contradicts established theories
        established_theories = [
            "conservation of energy",
            "second law of thermodynamics",
            "special relativity",
            "quantum mechanics",
            "natural selection",
        ]
        
        statement = hypothesis.get("statement", "").lower()
        
        for theory in established_theories:
            if any(word in statement for word in theory.split()):
                issues.append(f"Potential conflict with {theory}")
                alternatives.append(f"Alternative: {theory} may apply instead")
        
        # Check for extraordinary claims
        extraordinary_claims = [
            "faster than light",
            "perpetual motion",
            "absolute zero",
            "infinite energy",
        ]
        
        for claim in extraordinary_claims:
            if claim in statement:
                issues.append(f"Extraordinary claim: {claim} - requires extraordinary evidence")
        
        outcome = FalsificationOutcome.PARTIALLY_FALSIFIED if issues else FalsificationOutcome.NOT_FALSIFIED
        confidence = 0.7 if issues else 0.5
        
        return FalsificationResult(
            hypothesis_id=hypothesis.get("id", ""),
            method=FalsificationMethod.COMPARATIVE,
            outcome=outcome,
            confidence=confidence,
            evidence_for_falsification=evidence_for[:5],
            evidence_against_falsification=[],
            logical_issues=issues,
            statistical_issues=[],
            alternative_explanations=alternatives[:3],
            recommendations=["Compare predictions with established theories"],
            severity_assessment=len(issues) * 0.25,
        )
    
    def _predictive_falsification(
        self, hypothesis: Dict[str, Any], evidence: List[Dict[str, Any]]
    ) -> FalsificationResult:
        """Attempt predictive falsification."""
        predictions = hypothesis.get("testable_predictions", [])
        evidence_for = []
        evidence_against = []
        
        # Check if predictions are testable
        untestable = []
        for pred in predictions:
            if any(kw in pred.lower() for kw in ["unobservable", "hypothetical", "metaphysical"]):
                untestable.append(pred)
        
        issues = []
        if untestable:
            issues.append(f"{len(untestable)} predictions are untestable")
        
        if not predictions:
            issues.append("No testable predictions provided")
        
        # Check for failed predictions
        for ev in evidence:
            if not ev.get("supports_hypothesis", True):
                desc = ev.get("description", "")
                if any(pred.lower()[:20] in desc.lower() for pred in predictions):
                    evidence_for.append(f"Failed prediction: {desc}")
        
        outcome = FalsificationOutcome.FALSIFIED if evidence_for else FalsificationOutcome.NOT_FALSIFIED
        confidence = 0.8 if evidence_for else 0.5
        
        return FalsificationResult(
            hypothesis_id=hypothesis.get("id", ""),
            method=FalsificationMethod.PREDICTIVE,
            outcome=outcome,
            confidence=confidence,
            evidence_for_falsification=evidence_for[:5],
            evidence_against_falsification=evidence_against[:5],
            logical_issues=issues,
            statistical_issues=[],
            alternative_explanations=[],
            recommendations=["Design experiments to test specific predictions"],
            severity_assessment=0.4 if evidence_for else 0.1,
        )
    
    def _combine_results(
        self, hyp_id: str, results: List[FalsificationResult]
    ) -> FalsificationResult:
        """Combine results from multiple falsification methods."""
        # Count outcomes
        outcomes = [r.outcome for r in results]
        
        falsified_count = outcomes.count(FalsificationOutcome.FALSIFIED)
        not_falsified_count = outcomes.count(FalsificationOutcome.NOT_FALSIFIED)
        inconclusive_count = outcomes.count(FalsificationOutcome.INCONCLUSIVE)
        
        # Determine combined outcome
        if falsified_count >= 3:
            outcome = FalsificationOutcome.FALSIFIED
        elif falsified_count >= 2:
            outcome = FalsificationOutcome.PARTIALLY_FALSIFIED
        elif not_falsified_count >= 3:
            outcome = FalsificationOutcome.NOT_FALSIFIED
        else:
            outcome = FalsificationOutcome.INCONCLUSIVE
        
        # Combine evidence
        all_evidence_for = []
        all_evidence_against = []
        all_issues = []
        all_alternatives = []
        
        for r in results:
            all_evidence_for.extend(r.evidence_for_falsification)
            all_evidence_against.extend(r.evidence_against_falsification)
            all_issues.extend(r.logical_issues + r.statistical_issues)
            all_alternatives.extend(r.alternative_explanations)
        
        # Calculate combined confidence
        avg_confidence = statistics.mean([r.confidence for r in results])
        
        # Calculate severity
        max_severity = max(r.severity_assessment for r in results) if results else 0
        
        # Generate recommendations
        recommendations = self._generate_combined_recommendations(outcome, results)
        
        return FalsificationResult(
            hypothesis_id=hyp_id,
            method=FalsificationMethod.LOGICAL,  # Primary method
            outcome=outcome,
            confidence=avg_confidence,
            evidence_for_falsification=list(dict.fromkeys(all_evidence_for))[:5],
            evidence_against_falsification=list(dict.fromkeys(all_evidence_against))[:5],
            logical_issues=list(dict.fromkeys(all_issues))[:5],
            statistical_issues=[],
            alternative_explanations=list(dict.fromkeys(all_alternatives))[:3],
            recommendations=recommendations,
            severity_assessment=max_severity,
        )
    
    def _generate_logical_recommendations(self, issues: List[str]) -> List[str]:
        """Generate recommendations based on logical issues."""
        recs = []
        
        if any("contradictory" in i.lower() for i in issues):
            recs.append("Resolve contradictory assumptions before proceeding")
        
        if any("unfalsifiable" in i.lower() for i in issues):
            recs.append("Revise hypothesis to be empirically testable")
        
        if not recs:
            recs.append("No immediate logical issues detected")
        
        return recs[:3]
    
    def _generate_statistical_recommendations(self, issues: List[str]) -> List[str]:
        """Generate recommendations based on statistical issues."""
        recs = []
        
        if any("multiple testing" in i.lower() for i in issues):
            recs.append("Apply Bonferroni or FDR correction for multiple comparisons")
        
        if any("effect size" in i.lower() for i in issues):
            recs.append("Report effect sizes alongside p-values")
        
        if any("confidence interval" in i.lower() for i in issues):
            recs.append("Include confidence intervals in all statistical reports")
        
        return recs[:3]
    
    def _generate_combined_recommendations(
        self, outcome: FalsificationOutcome, results: List[FalsificationResult]
    ) -> List[str]:
        """Generate combined recommendations."""
        recommendations = []
        
        if outcome == FalsificationOutcome.FALSIFIED:
            recommendations.append("Hypothesis appears falsified - consider revision or rejection")
            recommendations.append("Review contradictory evidence carefully")
        elif outcome == FalsificationOutcome.PARTIALLY_FALSIFIED:
            recommendations.append("Hypothesis requires significant revision")
            recommendations.append("Focus on resolving identified issues")
        elif outcome == FalsificationOutcome.INCONCLUSIVE:
            recommendations.append("More evidence needed for definitive conclusion")
            recommendations.append("Consider designing targeted falsification experiments")
        else:
            recommendations.append("Hypothesis withstood falsification attempts")
            recommendations.append("Continue testing with new evidence")
        
        return recommendations[:4]
