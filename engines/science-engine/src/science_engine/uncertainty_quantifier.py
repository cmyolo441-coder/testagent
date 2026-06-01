"""Uncertainty Quantifier - Quantifies uncertainty in experimental results."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


class UncertaintyType(Enum):
    """Types of uncertainty."""
    STATISTICAL = "statistical"
    SYSTEMATIC = "systematic"
    MEASUREMENT = "measurement"
    MODEL = "model"
    PARAMETER = "parameter"
    SCENARIO = "scenario"
    EPISTEMIC = "epistemic"
    ALEATORIC = "aleatoric"


@dataclass
class ConfidenceInterval:
    """Confidence interval estimate."""
    lower: float
    upper: float
    confidence_level: float
    method: str
    
    @property
    def width(self) -> float:
        return self.upper - self.lower
    
    @property
    def center(self) -> float:
        return (self.lower + self.upper) / 2
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "lower": self.lower,
            "upper": self.upper,
            "confidence_level": self.confidence_level,
            "method": self.method,
            "width": self.width,
            "center": self.center,
        }


@dataclass
class UncertaintyMetrics:
    """Comprehensive uncertainty metrics."""
    mean: float
    std_dev: float
    variance: float
    confidence_intervals: Dict[str, ConfidenceInterval]
    standard_error: float
    coefficient_of_variation: float
    relative_uncertainty: float
    uncertainty_budget: Dict[str, float]
    sensitivity_indices: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mean": self.mean,
            "std_dev": self.std_dev,
            "variance": self.variance,
            "confidence_intervals": {k: v.to_dict() for k, v in self.confidence_intervals.items()},
            "standard_error": self.standard_error,
            "coefficient_of_variation": self.coefficient_of_variation,
            "relative_uncertainty": self.relative_uncertainty,
            "uncertainty_budget": self.uncertainty_budget,
            "sensitivity_indices": self.sensitivity_indices,
        }


class UncertaintyQuantifier:
    """Quantifies uncertainty in experimental results.
    
    Provides comprehensive uncertainty analysis including confidence intervals,
    sensitivity analysis, and uncertainty budgeting.
    """
    
    def __init__(self):
        self._metrics_cache: Dict[str, UncertaintyMetrics] = {}
    
    def quantify(self, results: Dict[str, Any]) -> UncertaintyMetrics:
        """Quantify uncertainty in results.
        
        Args:
            results: Dictionary containing experimental results
            
        Returns:
            UncertaintyMetrics with comprehensive uncertainty analysis
        """
        # Extract data
        data = results.get("data", [])
        measurements = results.get("measurements", {})
        
        if not data and measurements:
            # Convert measurements to data
            data = []
            for values in measurements.values():
                if isinstance(values, list):
                    data.extend(values)
        
        if not data:
            return self._empty_metrics()
        
        # Basic statistics
        mean_val = statistics.mean(data)
        std_val = statistics.stdev(data) if len(data) > 1 else 0.0
        var_val = statistics.variance(data) if len(data) > 1 else 0.0
        
        # Standard error
        n = len(data)
        std_error = std_val / math.sqrt(n) if n > 0 else 0.0
        
        # Coefficient of variation
        cv = (std_val / abs(mean_val) * 100) if mean_val != 0 else 0.0
        
        # Relative uncertainty
        rel_uncertainty = (std_val / abs(mean_val) * 100) if mean_val != 0 else 0.0
        
        # Confidence intervals
        ci_methods = {
            "95%": 0.95,
            "99%": 0.99,
            "90%": 0.90,
        }
        
        confidence_intervals = {}
        for level_name, level in ci_methods.items():
            ci = self._calculate_confidence_interval(data, level)
            confidence_intervals[level_name] = ci
        
        # Uncertainty budget
        uncertainty_budget = self._calculate_uncertainty_budget(results, data)
        
        # Sensitivity indices
        sensitivity = self._calculate_sensitivity_indices(results, data)
        
        metrics = UncertaintyMetrics(
            mean=mean_val,
            std_dev=std_val,
            variance=var_val,
            confidence_intervals=confidence_intervals,
            standard_error=std_error,
            coefficient_of_variation=cv,
            relative_uncertainty=rel_uncertainty,
            uncertainty_budget=uncertainty_budget,
            sensitivity_indices=sensitivity,
        )
        
        cache_key = str(hash(str(results)[:100]))
        self._metrics_cache[cache_key] = metrics
        
        return metrics
    
    def _calculate_confidence_interval(
        self, data: List[float], confidence_level: float
    ) -> ConfidenceInterval:
        """Calculate confidence interval for the mean."""
        n = len(data)
        if n < 2:
            return ConfidenceInterval(
                lower=data[0] if data else 0.0,
                upper=data[0] if data else 0.0,
                confidence_level=confidence_level,
                method="insufficient_data",
            )
        
        mean_val = statistics.mean(data)
        std_val = statistics.stdev(data)
        se = std_val / math.sqrt(n)
        
        # t-value approximation (for larger samples, use z)
        if n < 30:
            # Rough t-value approximation
            t_val = 2.0 + (1 - confidence_level) * 10
        else:
            # Z-value from confidence level
            z_values = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
            t_val = z_values.get(confidence_level, 1.96)
        
        margin = t_val * se
        
        return ConfidenceInterval(
            lower=mean_val - margin,
            upper=mean_val + margin,
            confidence_level=confidence_level,
            method="t_distribution" if n < 30 else "z_distribution",
        )
    
    def _calculate_uncertainty_budget(
        self, results: Dict[str, Any], data: List[float]
    ) -> Dict[str, float]:
        """Calculate uncertainty budget."""
        budget = {}
        
        # Statistical uncertainty
        if len(data) > 1:
            budget["statistical"] = statistics.stdev(data) / math.sqrt(len(data))
        
        # Measurement uncertainty (if provided)
        if "measurement_error" in results:
            budget["measurement"] = results["measurement_error"]
        
        # Systematic uncertainty (estimated)
        budget["systematic"] = 0.01 * abs(statistics.mean(data)) if data else 0.0
        
        # Model uncertainty (estimated)
        budget["model"] = 0.05 * abs(statistics.mean(data)) if data else 0.0
        
        # Normalize budget
        total = sum(budget.values())
        if total > 0:
            budget = {k: v / total for k, v in budget.items()}
        
        return budget
    
    def _calculate_sensitivity_indices(
        self, results: Dict[str, Any], data: List[float]
    ) -> Dict[str, float]:
        """Calculate sensitivity indices."""
        sensitivity = {}
        
        # Analyze sensitivity to different factors
        factors = ["sample_size", "measurement_error", "model_parameters"]
        
        base_std = statistics.stdev(data) if len(data) > 1 else 0.0
        
        for factor in factors:
            # Estimate sensitivity by perturbation
            if factor in results:
                perturbation = 0.1
                sensitivity[factor] = perturbation * base_std
            else:
                sensitivity[factor] = 0.0
        
        # Normalize
        total = sum(sensitivity.values())
        if total > 0:
            sensitivity = {k: v / total for k, v in sensitivity.items()}
        
        return sensitivity
    
    def _empty_metrics(self) -> UncertaintyMetrics:
        """Return empty metrics."""
        return UncertaintyMetrics(
            mean=0.0,
            std_dev=0.0,
            variance=0.0,
            confidence_intervals={},
            standard_error=0.0,
            coefficient_of_variation=0.0,
            relative_uncertainty=0.0,
            uncertainty_budget={},
            sensitivity_indices={},
        )
