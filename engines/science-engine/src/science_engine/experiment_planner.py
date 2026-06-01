"""Experiment Planner - Creates detailed experiment plans from hypotheses."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class ExperimentType(Enum):
    """Types of experiments."""
    CONTROLLED = "controlled"
    OBSERVATIONAL = "observational"
    QUASI_EXPERIMENTAL = "quasi_experimental"
    LONGITUDINAL = "longitudinal"
    CROSS_SECTIONAL = "cross_sectional"
    FIELD = "field"
    LABORATORY = "laboratory"
    NATURAL_EXPERIMENT = "natural_experiment"
    RANDOMIZED_CONTROLLED_TRIAL = "randomized_controlled_trial"


class StepType(Enum):
    """Types of experiment steps."""
    PREPARATION = "preparation"
    MEASUREMENT = "measurement"
    INTERVENTION = "intervention"
    OBSERVATION = "observation"
    REPLICATION = "replication"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"
    QUALITY_CHECK = "quality_check"


@dataclass
class ExperimentStep:
    """A single step in an experiment."""
    step_number: int
    step_type: StepType
    description: str
    duration: str
    required_resources: List[str]
    expected_output: str
    quality_criteria: List[str]
    dependencies: List[int]  # Step numbers this depends on
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "step_type": self.step_type.value,
            "description": self.description,
            "duration": self.duration,
            "required_resources": self.required_resources,
            "expected_output": self.expected_output,
            "quality_criteria": self.quality_criteria,
            "dependencies": self.dependencies,
        }


@dataclass
class ExperimentPlan:
    """Complete experiment plan."""
    id: str
    title: str
    hypothesis: str
    experiment_type: ExperimentType
    objectives: List[str]
    steps: List[ExperimentStep]
    variables: Dict[str, Dict[str, Any]]
    controls: List[str]
    sample_size: int
    randomization: str
    blinding: str
    ethics_considerations: List[str]
    timeline: str
    budget_estimate: Dict[str, float]
    risk_assessment: List[Dict[str, str]]
    success_metrics: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "hypothesis": self.hypothesis,
            "experiment_type": self.experiment_type.value,
            "objectives": self.objectives,
            "steps": [s.to_dict() for s in self.steps],
            "variables": self.variables,
            "controls": self.controls,
            "sample_size": self.sample_size,
            "randomization": self.randomization,
            "blinding": self.blinding,
            "ethics_considerations": self.ethics_considerations,
            "timeline": self.timeline,
            "budget_estimate": self.budget_estimate,
            "risk_assessment": self.risk_assessment,
            "success_metrics": self.success_metrics,
            "created_at": self.created_at.isoformat(),
        }


class ExperimentPlanner:
    """Creates detailed experiment plans from hypotheses.
    
    Translates scientific hypotheses into actionable experimental protocols
    with clear steps, controls, and success criteria.
    """
    
    def __init__(self):
        self._plans: Dict[str, ExperimentPlan] = {}
        self._counter = 0
    
    def plan(self, hypothesis: Dict[str, Any]) -> ExperimentPlan:
        """Create an experiment plan for testing a hypothesis.
        
        Args:
            hypothesis: Dictionary containing hypothesis information
            
        Returns:
            ExperimentPlan with detailed steps
        """
        self._counter += 1
        
        hyp_statement = hypothesis.get("statement", "Unknown hypothesis")
        hyp_type = hypothesis.get("type", "correlational")
        variables = hypothesis.get("variables", [])
        predictions = hypothesis.get("testable_predictions", [])
        
        # Determine experiment type
        exp_type = self._determine_experiment_type(hyp_type, hypothesis)
        
        # Generate objectives
        objectives = self._generate_objectives(hyp_statement, predictions)
        
        # Design variables
        var_design = self._design_variables(variables, hypothesis)
        
        # Generate steps
        steps = self._generate_steps(exp_type, var_design, hypothesis)
        
        # Determine sample size
        sample_size = self._calculate_sample_size(hypothesis)
        
        # Design randomization and blinding
        randomization = self._design_randomization(exp_type)
        blinding = self._design_blinding(exp_type)
        
        # Ethics considerations
        ethics = self._generate_ethics_considerations(hypothesis)
        
        # Timeline and budget
        timeline = self._estimate_timeline(steps)
        budget = self._estimate_budget(steps, sample_size)
        
        # Risks
        risks = self._assess_risks(hypothesis, steps)
        
        # Success metrics
        success_metrics = self._define_success_metrics(predictions)
        
        plan_id = f"EXP-{hashlib.md5(f'{hyp_statement[:50]}{self._counter}'.encode()).hexdigest()[:8].upper()}"
        
        plan = ExperimentPlan(
            id=plan_id,
            title=f"Experiment to test: {hyp_statement[:60]}...",
            hypothesis=hyp_statement,
            experiment_type=exp_type,
            objectives=objectives,
            steps=steps,
            variables=var_design,
            controls=self._identify_controls(var_design),
            sample_size=sample_size,
            randomization=randomization,
            blinding=blinding,
            ethics_considerations=ethics,
            timeline=timeline,
            budget_estimate=budget,
            risk_assessment=risks,
            success_metrics=success_metrics,
        )
        
        self._plans[plan_id] = plan
        return plan
    
    def _determine_experiment_type(
        self, hyp_type: str, hypothesis: Dict[str, Any]
    ) -> ExperimentType:
        """Determine appropriate experiment type."""
        if hyp_type == "causal":
            return ExperimentType.RANDOMIZED_CONTROLLED_TRIAL
        elif hyp_type == "correlational":
            return ExperimentType.OBSERVATIONAL
        elif hyp_type == "predictive":
            return ExperimentType.LONGITUDINAL
        elif hyp_type == "explanatory":
            return ExperimentType.LABORATORY
        else:
            return ExperimentType.CONTROLLED
    
    def _generate_objectives(
        self, hypothesis: str, predictions: List[str]
    ) -> List[str]:
        """Generate experiment objectives."""
        objectives = [
            f"Test the hypothesis: {hypothesis[:100]}",
            "Collect empirical evidence to support or refute the hypothesis",
            "Quantify the effect size and statistical significance",
        ]
        
        for pred in predictions[:3]:
            objectives.append(f"Verify prediction: {pred[:80]}")
        
        return objectives
    
    def _design_variables(
        self, variables: List[str], hypothesis: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Design experimental variables."""
        var_design = {}
        
        for i, var in enumerate(variables):
            if i == 0:
                var_design[var] = {
                    "type": "independent",
                    "role": "manipulated",
                    "measurement_method": "Direct manipulation",
                    "levels": ["low", "medium", "high"],
                }
            elif i == 1:
                var_design[var] = {
                    "type": "dependent",
                    "role": "measured",
                    "measurement_method": "Validated instrument",
                    "units": "standardized units",
                }
            else:
                var_design[var] = {
                    "type": "covariate",
                    "role": "controlled",
                    "measurement_method": "Controlled or statistically adjusted",
                }
        
        return var_design
    
    def _generate_steps(
        self,
        exp_type: ExperimentType,
        variables: Dict[str, Dict[str, Any]],
        hypothesis: Dict[str, Any],
    ) -> List[ExperimentStep]:
        """Generate experiment steps."""
        steps = []
        step_num = 1
        
        # Step 1: Preparation
        steps.append(ExperimentStep(
            step_number=step_num,
            step_type=StepType.PREPARATION,
            description="Prepare experimental materials and calibrate instruments",
            duration="1-2 days",
            required_resources=["Lab equipment", "Materials", "Calibration standards"],
            expected_output="Calibrated instruments and prepared materials",
            quality_criteria=["Calibration verified", "Materials inspected"],
            dependencies=[],
        ))
        step_num += 1
        
        # Step 2: Sample recruitment/selection
        steps.append(ExperimentStep(
            step_number=step_num,
            step_type=StepType.PREPARATION,
            description="Recruit and select experimental participants/samples",
            duration="1-2 weeks",
            required_resources=["Recruitment materials", "Screening tools"],
            expected_output="Enrolled sample meeting inclusion criteria",
            quality_criteria=["Sample size met", "Inclusion criteria satisfied"],
            dependencies=[1],
        ))
        step_num += 1
        
        # Step 3: Baseline measurement
        steps.append(ExperimentStep(
            step_number=step_num,
            step_type=StepType.MEASUREMENT,
            description="Collect baseline measurements for all variables",
            duration="1 day",
            required_resources=["Measurement instruments", "Data recording tools"],
            expected_output="Baseline data for all participants",
            quality_criteria=["All variables measured", "Data quality checked"],
            dependencies=[2],
        ))
        step_num += 1
        
        # Step 4: Intervention (if applicable)
        if exp_type in [
            ExperimentType.CONTROLLED,
            ExperimentType.RANDOMIZED_CONTROLLED_TRIAL,
            ExperimentType.LABORATORY,
        ]:
            iv_vars = [v for v, info in variables.items() if info.get("type") == "independent"]
            steps.append(ExperimentStep(
                step_number=step_num,
                step_type=StepType.INTERVENTION,
                description=f"Apply intervention manipulating: {', '.join(iv_vars[:3])}",
                duration="Variable based on intervention",
                required_resources=["Intervention materials", "Protocol documentation"],
                expected_output="Intervention applied consistently",
                quality_criteria=["Protocol followed", "Adherence documented"],
                dependencies=[3],
            ))
            step_num += 1
        
        # Step 5: Post-intervention measurement
        steps.append(ExperimentStep(
            step_number=step_num,
            step_type=StepType.MEASUREMENT,
            description="Collect post-intervention measurements",
            duration="1 day",
            required_resources=["Measurement instruments", "Data recording tools"],
            expected_output="Post-intervention data for all participants",
            quality_criteria=["All variables measured", "Timing consistent"],
            dependencies=[step_num - 1],
        ))
        step_num += 1
        
        # Step 6: Replication
        steps.append(ExperimentStep(
            step_number=step_num,
            step_type=StepType.REPLICATION,
            description="Repeat key measurements for reliability assessment",
            duration="1 day",
            required_resources=["Same as measurement"],
            expected_output="Replication data for reliability analysis",
            quality_criteria=["Same conditions", "Blinding maintained"],
            dependencies=[step_num - 1],
        ))
        step_num += 1
        
        # Step 7: Data quality check
        steps.append(ExperimentStep(
            step_number=step_num,
            step_type=StepType.QUALITY_CHECK,
            description="Perform quality checks on collected data",
            duration="0.5 day",
            required_resources=["Data analysis software"],
            expected_output="Quality-assured dataset",
            quality_criteria=["No missing data >5%", "Outliers identified"],
            dependencies=[step_num - 1],
        ))
        step_num += 1
        
        # Step 8: Analysis
        steps.append(ExperimentStep(
            step_number=step_num,
            step_type=StepType.ANALYSIS,
            description="Statistical analysis of experimental results",
            duration="2-3 days",
            required_resources=["Statistical software", "Analysis plan"],
            expected_output="Statistical results and effect sizes",
            quality_criteria=["Appropriate tests used", "Assumptions verified"],
            dependencies=[step_num - 1],
        ))
        step_num += 1
        
        # Step 9: Documentation
        steps.append(ExperimentStep(
            step_number=step_num,
            step_type=StepType.DOCUMENTATION,
            description="Document methods, results, and conclusions",
            duration="2-3 days",
            required_resources=["Documentation template"],
            expected_output="Complete experiment report",
            quality_criteria=["All sections complete", "Reproducible methods"],
            dependencies=[step_num - 1],
        ))
        
        return steps
    
    def _identify_controls(self, variables: Dict[str, Dict[str, Any]]) -> List[str]:
        """Identify control measures."""
        controls = []
        
        for var, info in variables.items():
            if info.get("type") == "dependent":
                controls.append(f"Measure {var} using validated instrument")
            elif info.get("type") == "covariate":
                controls.append(f"Control for {var} statistically or experimentally")
        
        controls.extend([
            "Random assignment to conditions",
            "Standardized procedures across all conditions",
            "Blinding of data collectors",
        ])
        
        return controls[:6]
    
    def _calculate_sample_size(self, hypothesis: Dict[str, Any]) -> int:
        """Calculate required sample size."""
        # Simplified power analysis
        effect_size = 0.5  # Medium effect size assumption
        alpha = 0.05
        power = 0.80
        
        # Rough estimate based on effect size
        base_n = int(16 / (effect_size ** 2))
        
        # Adjust for hypothesis confidence
        confidence = hypothesis.get("confidence", 0.5)
        adjustment = 1 + (1 - confidence) * 0.5
        
        return max(int(base_n * adjustment), 30)
    
    def _design_randomization(self, exp_type: ExperimentType) -> str:
        """Design randomization procedure."""
        if exp_type == ExperimentType.RANDOMIZED_CONTROLLED_TRIAL:
            return "Simple randomization using computer-generated random numbers"
        elif exp_type == ExperimentType.CONTROLLED:
            return "Alternate assignment or matched pairs"
        else:
            return "Observational - no randomization applied"
    
    def _design_blinding(self, exp_type: ExperimentType) -> str:
        """Design blinding procedure."""
        if exp_type in [
            ExperimentType.RANDOMIZED_CONTROLLED_TRIAL,
            ExperimentType.LABORATORY,
        ]:
            return "Double-blind: participants and data collectors blinded"
        elif exp_type == ExperimentType.CONTROLLED:
            return "Single-blind: data collectors blinded"
        else:
            return "Open-label: no blinding feasible"
    
    def _generate_ethics_considerations(self, hypothesis: Dict[str, Any]) -> List[str]:
        """Generate ethics considerations."""
        considerations = [
            "Obtain informed consent from all participants",
            "Ensure right to withdraw without penalty",
            "Protect participant confidentiality and data privacy",
            "Minimize potential risks and discomfort",
        ]
        
        # Add domain-specific considerations
        statement = hypothesis.get("statement", "").lower()
        if any(kw in statement for kw in ["human", "participant", "patient"]):
            considerations.append("Obtain IRB/ethics committee approval")
            considerations.append("Implement data anonymization procedures")
        
        if any(kw in statement for kw in ["animal", "specimen"]):
            considerations.append("Follow animal welfare guidelines")
            considerations.append("Minimize animal suffering")
        
        return considerations
    
    def _estimate_timeline(self, steps: List[ExperimentStep]) -> str:
        """Estimate overall timeline."""
        # Sum up durations (simplified)
        total_weeks = 8  # Base estimate
        
        if len(steps) > 8:
            total_weeks += 2
        if any(s.step_type == StepType.REPLICATION for s in steps):
            total_weeks += 2
        
        return f"Estimated {total_weeks} weeks from preparation to final report"
    
    def _estimate_budget(
        self, steps: List[ExperimentStep], sample_size: int
    ) -> Dict[str, float]:
        """Estimate budget."""
        return {
            "personnel": 5000.0,
            "equipment": 2000.0,
            "materials": 500.0 + sample_size * 10,
            "participant_compensation": sample_size * 50,
            "software": 500.0,
            "overhead": 3000.0,
            "total_estimate": 11000.0 + sample_size * 60,
        }
    
    def _assess_risks(
        self, hypothesis: Dict[str, Any], steps: List[ExperimentStep]
    ) -> List[Dict[str, str]]:
        """Assess experiment risks."""
        risks = [
            {
                "risk": "Low participation rate",
                "likelihood": "medium",
                "impact": "high",
                "mitigation": "Over-recruit by 20%",
            },
            {
                "risk": "Equipment malfunction",
                "likelihood": "low",
                "impact": "medium",
                "mitigation": "Have backup equipment available",
            },
            {
                "risk": "Data loss",
                "likelihood": "low",
                "impact": "high",
                "mitigation": "Regular backups and data validation",
            },
            {
                "risk": "Confounding variables",
                "likelihood": "medium",
                "impact": "high",
                "mitigation": "Randomization and statistical control",
            },
        ]
        
        return risks
    
    def _define_success_metrics(self, predictions: List[str]) -> List[str]:
        """Define success metrics."""
        metrics = [
            "Statistical significance (p < 0.05) for primary outcome",
            "Effect size ≥ 0.3 (medium effect)",
            "All predictions confirmed within confidence intervals",
            "Replication reliability > 0.7",
        ]
        
        for pred in predictions[:2]:
            metrics.append(f"Prediction verified: {pred[:60]}")
        
        return metrics
