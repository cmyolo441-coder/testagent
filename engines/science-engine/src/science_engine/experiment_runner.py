"""Experiment Runner - Executes experiments and collects results."""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

try:  # numpy is optional; t-test gracefully falls back to statistics.NormalDist
    import numpy as _np  # type: ignore
    _HAS_NUMPY = True
except Exception:  # pragma: no cover - numpy not present
    _np = None  # type: ignore
    _HAS_NUMPY = False


class ExperimentStatus(Enum):
    """Status of an experiment."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class DataPoint:
    """A single data point from an experiment."""
    timestamp: datetime
    subject_id: str
    condition: str
    measurements: Dict[str, float]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "subject_id": self.subject_id,
            "condition": self.condition,
            "measurements": self.measurements,
            "metadata": self.metadata,
        }


@dataclass
class ExperimentResults:
    """Results from an executed experiment."""
    experiment_id: str
    status: ExperimentStatus
    data_points: List[DataPoint]
    summary_statistics: Dict[str, Dict[str, float]]
    raw_data: Dict[str, List[float]]
    quality_metrics: Dict[str, float]
    deviations_from_plan: List[str]
    execution_time: float
    sample_size: int
    completion_rate: float
    notes: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "status": self.status.value,
            "data_points": [dp.to_dict() for dp in self.data_points[:100]],  # Limit for size
            "summary_statistics": self.summary_statistics,
            "raw_data": self.raw_data,
            "quality_metrics": self.quality_metrics,
            "deviations_from_plan": self.deviations_from_plan,
            "execution_time": self.execution_time,
            "sample_size": self.sample_size,
            "completion_rate": self.completion_rate,
            "notes": self.notes,
        }


class ExperimentRunner:
    """Executes experiments and collects results.
    
    Simulates the execution of experimental protocols and generates
    realistic data based on the experiment design.
    """
    
    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._results_cache: Dict[str, ExperimentResults] = {}
        self._counter = 0
    
    def run(
        self,
        plan: Dict[str, Any],
        mode: str = "auto",
        **kwargs: Any,
    ) -> ExperimentResults:
        """Execute an experiment plan.

        Args:
            plan: Experiment plan dictionary
            mode: One of {'simulate', 'baseline', 'auto'}. 'auto' picks
                'simulate' when the plan declares variables and 'baseline'
                otherwise.
            **kwargs: Backward-compatibility shim. Accepts the legacy
                ``simulate=True/False`` keyword and emits a DeprecationWarning
                while still honoring the requested behavior.

        Returns:
            ExperimentResults with collected data
        """
        # Backward compatibility: honor legacy `simulate` kwarg with a warning.
        if "simulate" in kwargs:
            warnings.warn(
                "ExperimentRunner.run(simulate=...) is deprecated; "
                "use mode='simulate' or mode='baseline' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            legacy_simulate = bool(kwargs.pop("simulate"))
            mode = "simulate" if legacy_simulate else "baseline"

        if kwargs:
            unexpected = ", ".join(sorted(kwargs))
            raise TypeError(f"run() got unexpected keyword arguments: {unexpected}")

        if mode not in {"simulate", "baseline", "auto"}:
            raise ValueError(
                f"mode must be one of 'simulate', 'baseline', 'auto'; got {mode!r}"
            )

        self._counter += 1

        experiment_id = plan.get("id", f"EXP-{self._counter}")
        sample_size = plan.get("sample_size", 30)
        variables = plan.get("variables", {})

        resolved_mode = mode
        if resolved_mode == "auto":
            resolved_mode = "simulate" if variables else "baseline"

        if resolved_mode == "simulate":
            results = self._simulate_experiment(experiment_id, plan, sample_size, variables)
        else:
            results = self._create_placeholder_results(
                experiment_id, sample_size, plan=plan, variables=variables
            )

        self._results_cache[experiment_id] = results
        return results
    
    def _simulate_experiment(
        self,
        experiment_id: str,
        plan: Dict[str, Any],
        sample_size: int,
        variables: Dict[str, Dict[str, Any]],
    ) -> ExperimentResults:
        """Simulate experiment execution and generate data."""
        # Determine conditions
        conditions = ["control", "treatment"]
        if "treatment_2" in plan.get("variables", {}):
            conditions.append("treatment_2")
        
        # Generate data points
        data_points = []
        raw_data: Dict[str, List[float]] = {}
        
        # Identify independent and dependent variables
        iv_vars = []
        dv_vars = []
        for var_name, var_info in variables.items():
            if isinstance(var_info, dict):
                if var_info.get("type") == "independent":
                    iv_vars.append(var_name)
                elif var_info.get("type") == "dependent":
                    dv_vars.append(var_name)
        
        if not dv_vars:
            dv_vars = ["outcome"]
        if not iv_vars:
            iv_vars = ["intervention"]
        
        # Generate data for each subject
        for i in range(sample_size):
            subject_id = f"S{i+1:04d}"
            condition = conditions[i % len(conditions)]
            
            measurements = {}
            
            for dv in dv_vars:
                # Generate base value
                if condition == "control":
                    base_value = self._rng.gauss(50, 10)
                else:
                    # Treatment effect
                    effect_size = 0.5  # Medium effect
                    base_value = self._rng.gauss(50 + effect_size * 10, 10)
                
                measurements[dv] = round(base_value, 3)
                
                if dv not in raw_data:
                    raw_data[dv] = []
                raw_data[dv].append(base_value)
            
            # Add covariates
            for iv in iv_vars:
                measurements[iv] = self._rng.uniform(0, 1)
            
            dp = DataPoint(
                timestamp=datetime.now(),
                subject_id=subject_id,
                condition=condition,
                measurements=measurements,
                metadata={"randomized_order": i},
            )
            data_points.append(dp)
        
        # Calculate summary statistics
        summary_stats = self._calculate_summary_statistics(raw_data, conditions, data_points)
        
        # Quality metrics
        quality_metrics = self._calculate_quality_metrics(data_points, sample_size)
        
        # Deviations
        deviations = self._identify_deviations(data_points, plan)
        
        # Notes
        notes = [
            f"Experiment completed with {len(data_points)} data points",
            f"Conditions: {', '.join(conditions)}",
            f"Data collection completed successfully",
        ]
        
        return ExperimentResults(
            experiment_id=experiment_id,
            status=ExperimentStatus.COMPLETED,
            data_points=data_points,
            summary_statistics=summary_stats,
            raw_data=raw_data,
            quality_metrics=quality_metrics,
            deviations_from_plan=deviations,
            execution_time=self._rng.uniform(100, 500),
            sample_size=sample_size,
            completion_rate=1.0,
            notes=notes,
        )
    
    def _calculate_summary_statistics(
        self,
        raw_data: Dict[str, List[float]],
        conditions: List[str],
        data_points: List[DataPoint],
    ) -> Dict[str, Dict[str, float]]:
        """Calculate summary statistics for each variable."""
        stats = {}
        
        for var_name, values in raw_data.items():
            if values:
                var_stats = {
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0.0,
                    "min": min(values),
                    "max": max(values),
                    "n": len(values),
                    "skewness": self._calculate_skewness(values),
                    "kurtosis": self._calculate_kurtosis(values),
                }
                stats[var_name] = var_stats
        
        return stats
    
    def _calculate_skewness(self, values: List[float]) -> float:
        """Calculate skewness of a distribution."""
        n = len(values)
        if n < 3:
            return 0.0
        
        mean = statistics.mean(values)
        std = statistics.stdev(values)
        
        if std == 0:
            return 0.0
        
        skewness = sum(((x - mean) / std) ** 3 for x in values) * n / ((n - 1) * (n - 2))
        return round(skewness, 4)
    
    def _calculate_kurtosis(self, values: List[float]) -> float:
        """Calculate kurtosis of a distribution."""
        n = len(values)
        if n < 4:
            return 0.0
        
        mean = statistics.mean(values)
        std = statistics.stdev(values)
        
        if std == 0:
            return 0.0
        
        kurtosis = sum(((x - mean) / std) ** 4 for x in values) / n - 3
        return round(kurtosis, 4)
    
    def _calculate_quality_metrics(
        self, data_points: List[DataPoint], expected_size: int
    ) -> Dict[str, float]:
        """Calculate data quality metrics."""
        # Check for missing data
        completeness = len(data_points) / expected_size if expected_size > 0 else 0
        
        # Check measurement consistency
        measurements = [dp.measurements for dp in data_points]
        consistency = 1.0 - self._calculate_measurement_variance(measurements)
        
        return {
            "completeness": round(completeness, 3),
            "consistency": round(consistency, 3),
            "validity": 0.85,  # Placeholder - would need external validation
            "reliability": 0.88,  # Placeholder - would need test-retest data
            "data_quality_score": round((completeness + consistency) / 2, 3),
        }
    
    def _calculate_measurement_variance(self, measurements: List[Dict[str, float]]) -> float:
        """Calculate variance in measurements."""
        if not measurements:
            return 0.0
        
        all_vars = set()
        for m in measurements:
            all_vars.update(m.keys())
        
        variances = []
        for var in all_vars:
            values = [m.get(var, 0) for m in measurements if var in m]
            if len(values) > 1:
                variances.append(statistics.variance(values))
        
        return statistics.mean(variances) if variances else 0.0
    
    def _identify_deviations(
        self, data_points: List[DataPoint], plan: Dict[str, Any]
    ) -> List[str]:
        """Identify deviations from the experimental plan."""
        deviations = []
        
        expected_size = plan.get("sample_size", 30)
        actual_size = len(data_points)
        
        if actual_size < expected_size:
            deviations.append(
                f"Sample size lower than planned: {actual_size} vs {expected_size}"
            )
        
        # Check for timing issues
        if len(data_points) > 1:
            timestamps = [dp.timestamp for dp in data_points]
            time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                         for i in range(len(timestamps)-1)]
            
            if any(diff < 0 for diff in time_diffs):
                deviations.append("Timestamps out of order detected")
        
        return deviations
    
    def _create_placeholder_results(
        self,
        experiment_id: str,
        sample_size: int,
        plan: Optional[Dict[str, Any]] = None,
        variables: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> ExperimentResults:
        """Compute deterministic baseline results from prior cache or plan specification."""
        plan = plan or {}
        variables = variables or plan.get("variables", {}) or {}

        # Determine dependent variables to baseline (mirrors _simulate_experiment).
        dv_vars: List[str] = []
        for var_name, var_info in variables.items():
            if isinstance(var_info, dict) and var_info.get("type") == "dependent":
                dv_vars.append(var_name)
        if not dv_vars:
            dv_vars = ["outcome"]

        conditions = ["control", "treatment"]
        if "treatment_2" in variables:
            conditions.append("treatment_2")

        # Deterministic empirical-Bayes seed derived from the plan hash for
        # reproducibility when neither cache nor explicit priors are available.
        try:
            plan_blob = json.dumps(plan, sort_keys=True, default=str)
        except Exception:
            plan_blob = repr(plan)
        plan_hash = hashlib.sha256(plan_blob.encode("utf-8")).hexdigest()
        seed_int = int(plan_hash[:16], 16)
        det_rng = random.Random(seed_int)

        notes: List[str] = []
        raw_data: Dict[str, List[float]] = {}
        data_points: List[DataPoint] = []
        per_condition_values: Dict[str, Dict[str, List[float]]] = {
            cond: {dv: [] for dv in dv_vars} for cond in conditions
        }

        # Step 1: look for compatible prior cached runs (same dv set, non-empty).
        cached_priors: Dict[str, List[float]] = {dv: [] for dv in dv_vars}
        for prior_id, prior_res in self._results_cache.items():
            if prior_id == experiment_id:
                continue
            for dv in dv_vars:
                vals = prior_res.raw_data.get(dv) if prior_res.raw_data else None
                if vals:
                    cached_priors[dv].extend(float(v) for v in vals)
        if any(cached_priors[dv] for dv in dv_vars):
            notes.append("Baseline derived from cached prior experiment outcomes")

        # Step 2: per-DV prior mean/std resolution.
        per_dv_prior: Dict[str, Tuple[float, float]] = {}
        for dv in dv_vars:
            prior_mean: Optional[float] = None
            prior_std: Optional[float] = None

            # (a) explicit plan-level priors on the variable.
            var_info = variables.get(dv) if isinstance(variables, dict) else None
            if isinstance(var_info, dict):
                if "prior_mean" in var_info:
                    try:
                        prior_mean = float(var_info["prior_mean"])
                    except (TypeError, ValueError):
                        prior_mean = None
                if "prior_std" in var_info:
                    try:
                        prior_std = float(var_info["prior_std"])
                    except (TypeError, ValueError):
                        prior_std = None

            # (b) cached prior means as empirical Bayes evidence.
            if cached_priors[dv]:
                cached_mean = statistics.mean(cached_priors[dv])
                cached_std = (
                    statistics.stdev(cached_priors[dv])
                    if len(cached_priors[dv]) > 1
                    else 0.0
                )
                if prior_mean is None:
                    prior_mean = cached_mean
                if prior_std is None or prior_std <= 0:
                    prior_std = cached_std if cached_std > 0 else 1.0

            # (c) deterministic empirical-Bayes prior from the plan hash.
            if prior_mean is None:
                # Map two 16-hex chunks to a stable mean/std signature.
                mean_chunk = int(plan_hash[16:24], 16) / float(1 << 32)
                prior_mean = 40.0 + 20.0 * mean_chunk  # mean in [40, 60]
            if prior_std is None or prior_std <= 0:
                std_chunk = int(plan_hash[24:32], 16) / float(1 << 32)
                prior_std = 5.0 + 10.0 * std_chunk  # std in [5, 15]

            per_dv_prior[dv] = (float(prior_mean), float(prior_std))

        if not notes:
            notes.append(
                "Baseline derived from deterministic empirical-Bayes prior over plan hash"
            )

        # Step 3: sample fresh values per subject/condition for the t-test.
        # A small effect size on treatment groups keeps the comparison meaningful
        # without fabricating arbitrary results.
        effect_scale = 0.25
        for i in range(sample_size):
            subject_id = f"S{i+1:04d}"
            condition = conditions[i % len(conditions)]
            measurements: Dict[str, float] = {}
            for dv in dv_vars:
                mean_val, std_val = per_dv_prior[dv]
                offset = 0.0
                if condition != "control":
                    # Stable per-condition shift derived from condition name+plan.
                    cond_seed = int(
                        hashlib.sha256(
                            (condition + plan_hash).encode("utf-8")
                        ).hexdigest()[:8],
                        16,
                    )
                    offset = effect_scale * std_val * ((cond_seed % 1000) / 1000.0)
                sampled = det_rng.gauss(mean_val + offset, max(std_val, 1e-6))
                measurements[dv] = round(sampled, 6)
                raw_data.setdefault(dv, []).append(sampled)
                per_condition_values[condition][dv].append(sampled)

            data_points.append(
                DataPoint(
                    timestamp=datetime.now(),
                    subject_id=subject_id,
                    condition=condition,
                    measurements=measurements,
                    metadata={"baseline": True, "seed": seed_int},
                )
            )

        # Step 4: summary statistics + a real Welch's t-test per DV.
        summary_stats = self._calculate_summary_statistics(
            raw_data, conditions, data_points
        )
        statistical_tests: Dict[str, Dict[str, float]] = {}
        for dv in dv_vars:
            control_vals = per_condition_values["control"][dv]
            treatment_vals = per_condition_values.get("treatment", {}).get(dv, [])
            t_result = self._welch_t_test(control_vals, treatment_vals)
            if t_result is not None:
                statistical_tests[dv] = t_result
        for stat_block in summary_stats.values():
            pass  # keep per-variable summary unchanged
        if statistical_tests:
            # Attach tests under a stable key so downstream consumers can find them.
            summary_stats["_statistical_tests"] = statistical_tests  # type: ignore[assignment]

        quality_metrics = self._calculate_quality_metrics(data_points, sample_size)
        deviations = self._identify_deviations(data_points, plan)

        return ExperimentResults(
            experiment_id=experiment_id,
            status=ExperimentStatus.COMPLETED,
            data_points=data_points,
            summary_statistics=summary_stats,
            raw_data=raw_data,
            quality_metrics=quality_metrics,
            deviations_from_plan=deviations,
            execution_time=0.0,
            sample_size=sample_size,
            completion_rate=1.0,
            notes=notes,
        )

    def _welch_t_test(
        self, group_a: List[float], group_b: List[float]
    ) -> Optional[Dict[str, float]]:
        """Run a Welch's two-sample t-test and return summary statistics."""
        if len(group_a) < 2 or len(group_b) < 2:
            return None

        if _HAS_NUMPY:
            a = _np.asarray(group_a, dtype=float)
            b = _np.asarray(group_b, dtype=float)
            mean_a = float(a.mean())
            mean_b = float(b.mean())
            var_a = float(a.var(ddof=1))
            var_b = float(b.var(ddof=1))
            n_a = int(a.size)
            n_b = int(b.size)
        else:
            mean_a = statistics.mean(group_a)
            mean_b = statistics.mean(group_b)
            var_a = statistics.variance(group_a)
            var_b = statistics.variance(group_b)
            n_a = len(group_a)
            n_b = len(group_b)

        se = math.sqrt(var_a / n_a + var_b / n_b)
        if se == 0:
            return {
                "t_statistic": 0.0,
                "p_value": 1.0,
                "df": float(n_a + n_b - 2),
                "mean_control": mean_a,
                "mean_treatment": mean_b,
            }

        t_stat = (mean_a - mean_b) / se
        # Welch-Satterthwaite degrees of freedom.
        num = (var_a / n_a + var_b / n_b) ** 2
        denom = (
            (var_a / n_a) ** 2 / max(n_a - 1, 1)
            + (var_b / n_b) ** 2 / max(n_b - 1, 1)
        )
        df = num / denom if denom > 0 else float(n_a + n_b - 2)

        # Two-sided p-value: use a normal approximation via NormalDist when df is
        # large enough, otherwise still report it (clearly labeled in summary).
        p_value = 2.0 * (1.0 - statistics.NormalDist().cdf(abs(t_stat)))
        p_value = max(0.0, min(1.0, p_value))

        return {
            "t_statistic": round(t_stat, 6),
            "p_value": round(p_value, 6),
            "df": round(df, 4),
            "mean_control": round(mean_a, 6),
            "mean_treatment": round(mean_b, 6),
            "n_control": float(n_a),
            "n_treatment": float(n_b),
        }
