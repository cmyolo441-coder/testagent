"""Simulation Designer - Designs computational simulations for scientific experiments."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


class SimulationType(Enum):
    """Types of simulations."""
    MONTE_CARLO = "monte_carlo"
    AGENT_BASED = "agent_based"
    SYSTEM_DYNAMICS = "system_dynamics"
    DISCRETE_EVENT = "discrete_event"
    CONTINUOUS = "continuous"
    HYBRID = "hybrid"
    STOCHASTIC = "stochastic"
    DETERMINISTIC = "deterministic"


class OutputFormat(Enum):
    """Output formats for simulation results."""
    NUMERICAL = "numerical"
    VISUALIZATION = "visualization"
    STATISTICAL = "statistical"
    TIME_SERIES = "time_series"
    DISTRIBUTION = "distribution"


@dataclass
class SimulationConfig:
    """Configuration for a simulation."""
    simulation_type: SimulationType
    duration: float
    time_step: float
    num_runs: int
    random_seed: Optional[int]
    parameters: Dict[str, Any]
    output_formats: List[OutputFormat]
    convergence_criteria: Optional[str]
    validation_method: Optional[str]


@dataclass
class SimulationPlan:
    """Plan for executing a simulation."""
    id: str
    name: str
    description: str
    hypothesis_id: str
    config: SimulationConfig
    input_variables: Dict[str, str]
    output_variables: Dict[str, str]
    control_variables: Dict[str, str]
    success_criteria: List[str]
    estimated_runtime: str
    resource_requirements: Dict[str, Any]
    validation_plan: str
    analysis_plan: str
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "hypothesis_id": self.hypothesis_id,
            "config": {
                "simulation_type": self.config.simulation_type.value,
                "duration": self.config.duration,
                "time_step": self.config.time_step,
                "num_runs": self.config.num_runs,
                "random_seed": self.config.random_seed,
                "parameters": self.config.parameters,
                "output_formats": [f.value for f in self.config.output_formats],
            },
            "input_variables": self.input_variables,
            "output_variables": self.output_variables,
            "control_variables": self.control_variables,
            "success_criteria": self.success_criteria,
            "estimated_runtime": self.estimated_runtime,
            "resource_requirements": self.resource_requirements,
            "validation_plan": self.validation_plan,
            "analysis_plan": self.analysis_plan,
            "created_at": self.created_at.isoformat(),
        }


class SimulationDesigner:
    """Designs computational simulations for scientific experiments.
    
    Creates detailed simulation plans that can be used to test hypotheses
    and explore theoretical predictions through computational modeling.
    """
    
    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._simulations: Dict[str, SimulationPlan] = {}
        self._counter = 0
    
    def design(
        self,
        experiment_params: Dict[str, Any],
        hypothesis_id: str = "default"
    ) -> SimulationPlan:
        """Design a simulation based on experiment parameters.
        
        Args:
            experiment_params: Parameters including variables, domain, hypotheses
            hypothesis_id: ID of hypothesis being tested
            
        Returns:
            SimulationPlan with detailed configuration
        """
        self._counter += 1
        
        # Extract parameters
        variables = experiment_params.get("variables", {})
        domain = experiment_params.get("domain", "general")
        hypothesis = experiment_params.get("hypothesis", "")
        constraints = experiment_params.get("constraints", [])
        
        # Determine simulation type
        sim_type = self._determine_simulation_type(experiment_params)
        
        # Design configuration
        config = self._design_config(sim_type, experiment_params)
        
        # Classify variables
        input_vars, output_vars, control_vars = self._classify_variables(variables)
        
        # Generate success criteria
        success_criteria = self._generate_success_criteria(hypothesis, variables)
        
        # Estimate runtime
        runtime = self._estimate_runtime(config)
        
        # Resource requirements
        resources = self._estimate_resources(config)
        
        # Validation plan
        validation_plan = self._create_validation_plan(sim_type, hypothesis)
        
        # Analysis plan
        analysis_plan = self._create_analysis_plan(output_vars, experiment_params)
        
        sim_id = f"SIM-{hashlib.md5(f'{hypothesis_id}{self._counter}'.encode()).hexdigest()[:8].upper()}"
        
        plan = SimulationPlan(
            id=sim_id,
            name=f"Simulation for {domain} hypothesis",
            description=self._generate_description(hypothesis, sim_type),
            hypothesis_id=hypothesis_id,
            config=config,
            input_variables=input_vars,
            output_variables=output_vars,
            control_variables=control_vars,
            success_criteria=success_criteria,
            estimated_runtime=runtime,
            resource_requirements=resources,
            validation_plan=validation_plan,
            analysis_plan=analysis_plan,
        )
        
        self._simulations[sim_id] = plan
        return plan
    
    def _determine_simulation_type(self, params: Dict[str, Any]) -> SimulationType:
        """Determine appropriate simulation type."""
        domain = params.get("domain", "").lower()
        variables = params.get("variables", {})
        hypothesis = params.get("hypothesis", "").lower()
        
        # Check for stochastic elements
        has_stochastic = any(
            "random" in str(v).lower() or "stochastic" in str(v).lower()
            for v in variables.values()
        )
        
        # Check for agent-based modeling needs
        has_agents = any(
            kw in hypothesis
            for kw in ["agent", "individual", "actor", "population"]
        )
        
        # Check for discrete events
        has_discrete = any(
            kw in hypothesis
            for kw in ["event", "arrival", "queue", "transaction"]
        )
        
        if has_agents:
            return SimulationType.AGENT_BASED
        elif has_discrete:
            return SimulationType.DISCRETE_EVENT
        elif has_stochastic:
            return SimulationType.STOCHASTIC
        elif "biological" in domain or "ecological" in domain:
            return SimulationType.SYSTEM_DYNAMICS
        else:
            return SimulationType.MONTE_CARLO
    
    def _design_config(
        self, sim_type: SimulationType, params: Dict[str, Any]
    ) -> SimulationConfig:
        """Design simulation configuration."""
        # Duration and time step based on type
        duration_map = {
            SimulationType.MONTE_CARLO: 1000,
            SimulationType.AGENT_BASED: 100,
            SimulationType.SYSTEM_DYNAMICS: 50,
            SimulationType.DISCRETE_EVENT: 500,
            SimulationType.CONTINUOUS: 100,
            SimulationType.STOCHASTIC: 1000,
            SimulationType.DETERMINISTIC: 100,
            SimulationType.HYBRID: 200,
        }
        
        duration = duration_map.get(sim_type, 100)
        time_step = duration / 1000  # Default to 1000 steps
        
        num_runs = 30 if sim_type in [
            SimulationType.MONTE_CARLO,
            SimulationType.STOCHASTIC
        ] else 10
        
        # Build parameters from experiment params
        sim_params = {}
        for key, value in params.get("variables", {}).items():
            if isinstance(value, dict):
                sim_params[key] = value
            else:
                sim_params[key] = {"initial": value, "range": [0, 100]}
        
        # Add domain-specific parameters
        if "parameters" in params:
            sim_params.update(params["parameters"])
        
        output_formats = [OutputFormat.NUMERICAL, OutputFormat.STATISTICAL]
        if params.get("visualize", True):
            output_formats.append(OutputFormat.VISUALIZATION)
        
        convergence = "Relative change < 1e-6 for 100 consecutive steps"
        if sim_type == SimulationType.MONTE_CARLO:
            convergence = "Variance of estimates < 0.01"
        
        return SimulationConfig(
            simulation_type=sim_type,
            duration=duration,
            time_step=time_step,
            num_runs=num_runs,
            random_seed=self._rng.randint(0, 2**31),
            parameters=sim_params,
            output_formats=output_formats,
            convergence_criteria=convergence,
            validation_method="Comparison with analytical solutions where available",
        )
    
    def _classify_variables(
        self, variables: Dict[str, Any]
    ) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """Classify variables into input, output, and control."""
        input_vars = {}
        output_vars = {}
        control_vars = {}
        
        for var_name, var_info in variables.items():
            if isinstance(var_info, dict):
                var_type = var_info.get("type", "input").lower()
                description = var_info.get("description", f"Variable {var_name}")
            else:
                var_type = "input"
                description = str(var_info)
            
            if var_type in ("output", "result", "dependent"):
                output_vars[var_name] = description
            elif var_type in ("control", "fixed", "constant"):
                control_vars[var_name] = description
            else:
                input_vars[var_name] = description
        
        # Ensure we have at least one output
        if not output_vars and input_vars:
            first_input = list(input_vars.keys())[0]
            output_vars[f"result_of_{first_input}"] = "Primary output measure"
        
        return input_vars, output_vars, control_vars
    
    def _generate_success_criteria(
        self, hypothesis: str, variables: Dict[str, Any]
    ) -> List[str]:
        """Generate success criteria for the simulation."""
        criteria = []
        
        # Standard criteria
        criteria.append("Simulation converges to stable solution")
        criteria.append("Results are reproducible across multiple runs")
        
        # Hypothesis-specific criteria
        if hypothesis:
            criteria.append(f"Hypothesis predictions are supported within confidence bounds")
        
        # Variable-specific criteria
        output_vars = [v for v, info in variables.items() 
                      if isinstance(info, dict) and info.get("type") == "output"]
        
        for var in output_vars[:3]:
            criteria.append(f"Output variable {var} shows expected behavior")
        
        # Statistical criteria
        criteria.append("Statistical significance achieved (p < 0.05)")
        criteria.append("Effect size is practically meaningful")
        
        return criteria[:6]
    
    def _estimate_runtime(self, config: SimulationConfig) -> str:
        """Estimate simulation runtime."""
        base_time = config.duration / config.time_step
        runs_factor = config.num_runs
        
        # Rough estimate in seconds
        if config.simulation_type == SimulationType.AGENT_BASED:
            estimated_seconds = base_time * runs_factor * 0.01
        elif config.simulation_type == SimulationType.MONTE_CARLO:
            estimated_seconds = base_time * runs_factor * 0.001
        else:
            estimated_seconds = base_time * runs_factor * 0.005
        
        if estimated_seconds < 60:
            return f"~{int(estimated_seconds)} seconds"
        elif estimated_seconds < 3600:
            return f"~{int(estimated_seconds / 60)} minutes"
        else:
            return f"~{int(estimated_seconds / 3600)} hours"
    
    def _estimate_resources(self, config: SimulationConfig) -> Dict[str, Any]:
        """Estimate resource requirements."""
        base_memory = 100  # MB
        
        if config.simulation_type == SimulationType.AGENT_BASED:
            memory_per_agent = 0.1  # MB
            num_agents = config.parameters.get("num_agents", 1000)
            memory = base_memory + num_agents * memory_per_agent
        else:
            memory = base_memory * (1 + config.num_runs * 0.1)
        
        return {
            "memory_mb": int(memory),
            "cpu_cores": min(config.num_runs, 8),
            "storage_mb": int(memory * 0.5),
            "gpu_recommended": config.simulation_type == SimulationType.AGENT_BASED,
        }
    
    def _create_validation_plan(self, sim_type: SimulationType, hypothesis: str) -> str:
        """Create validation plan for the simulation."""
        plan_parts = [
            "VALIDATION PLAN",
            "=" * 40,
            "",
            "1. Verification:",
            "   - Code review and unit testing",
            "   - Comparison with analytical solutions where available",
            "   - Boundary condition testing",
            "",
            "2. Validation:",
            "   - Sensitivity analysis of key parameters",
            "   - Cross-validation with historical data",
            "   - Expert review of model assumptions",
            "",
            "3. Credibility Assessment:",
        ]
        
        if sim_type == SimulationType.MONTE_CARLO:
            plan_parts.append("   - Convergence analysis")
            plan_parts.append("   - Variance reduction techniques evaluation")
        elif sim_type == SimulationType.AGENT_BASED:
            plan_parts.append("   - Agent behavior validation against empirical data")
            plan_parts.append("   - Emergent properties verification")
        else:
            plan_parts.append("   - Numerical stability analysis")
            plan_parts.append("   - Conservation law verification")
        
        return "\n".join(plan_parts)
    
    def _create_analysis_plan(
        self, output_vars: Dict[str, Any], params: Dict[str, Any]
    ) -> str:
        """Create analysis plan for simulation results."""
        plan = [
            "ANALYSIS PLAN",
            "=" * 40,
            "",
            "1. Descriptive Statistics:",
            "   - Mean, median, standard deviation for all output variables",
            "   - Distribution fitting for stochastic outputs",
            "",
            "2. Inferential Statistics:",
            "   - Hypothesis testing using t-tests or ANOVA as appropriate",
            "   - Confidence interval estimation",
            "   - Effect size calculation",
            "",
            "3. Sensitivity Analysis:",
            "   - One-at-a-time sensitivity analysis",
            "   - Sobol indices for global sensitivity",
            "",
            "4. Visualization:",
            "   - Time series plots for dynamic outputs",
            "   - Scatter plots for variable relationships",
            "   - Distribution plots for stochastic outputs",
        ]
        
        if output_vars:
            var_list = list(output_vars.keys())[:5]
            plan.append(f"\n5. Variable-Specific Analysis:")
            for var in var_list:
                plan.append(f"   - Analyze {var} with appropriate statistical methods")
        
        return "\n".join(plan)
    
    def _generate_description(self, hypothesis: str, sim_type: SimulationType) -> str:
        """Generate simulation description."""
        desc = f"Computational simulation using {sim_type.value} methodology"
        if hypothesis:
            desc += f" to test the hypothesis: {hypothesis[:100]}"
        return desc
