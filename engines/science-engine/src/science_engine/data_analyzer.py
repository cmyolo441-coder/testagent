"""Data Analyzer - Analyzes experimental data and tests hypotheses."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


class TestType(Enum):
    """Types of statistical tests."""
    T_TEST_INDEPENDENT = "t_test_independent"
    T_TEST_PAIRED = "t_test_paired"
    T_TEST_ONE_SAMPLE = "t_test_one_sample"
    ANOVA_ONE_WAY = "anova_one_way"
    ANOVA_TWO_WAY = "anova_two_way"
    CHI_SQUARE = "chi_square"
    CORRELATION_PEARSON = "correlation_pearson"
    CORRELATION_SPEARMAN = "correlation_spearman"
    REGRESSION_LINEAR = "regression_linear"
    REGRESSION_LOGISTIC = "regression_logistic"
    MANN_WHITNEY = "mann_whitney"
    WILCOXON = "wilcoxon"
    KRUSKAL_WALLIS = "kruskal_wallis"


@dataclass
class StatisticalTest:
    """Result of a statistical test."""
    test_type: TestType
    test_name: str
    statistic: float
    p_value: float
    effect_size: float
    confidence_interval: Tuple[float, float]
    degrees_of_freedom: Optional[int]
    interpretation: str
    significant: bool
    assumptions_met: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_type": self.test_type.value,
            "test_name": self.test_name,
            "statistic": self.statistic,
            "p_value": self.p_value,
            "effect_size": self.effect_size,
            "confidence_interval": list(self.confidence_interval),
            "degrees_of_freedom": self.degrees_of_freedom,
            "interpretation": self.interpretation,
            "significant": self.significant,
            "assumptions_met": self.assumptions_met,
        }


@dataclass
class AnalysisResults:
    """Complete analysis results."""
    hypothesis_id: str
    descriptive_stats: Dict[str, Dict[str, float]]
    statistical_tests: List[StatisticalTest]
    effect_sizes: Dict[str, float]
    assumptions_checks: Dict[str, bool]
    recommendations: List[str]
    conclusion: str
    confidence_level: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "descriptive_stats": self.descriptive_stats,
            "statistical_tests": [t.to_dict() for t in self.statistical_tests],
            "effect_sizes": self.effect_sizes,
            "assumptions_checks": self.assumptions_checks,
            "recommendations": self.recommendations,
            "conclusion": self.conclusion,
            "confidence_level": self.confidence_level,
        }


class DataAnalyzer:
    """Analyzes experimental data and tests hypotheses.
    
    Performs comprehensive statistical analysis including descriptive
    statistics, hypothesis testing, effect size calculation, and
    assumption checking.
    """
    
    ALPHA = 0.05  # Significance level
    
    def __init__(self):
        self._analyses: Dict[str, AnalysisResults] = {}
    
    def analyze(
        self,
        data: Dict[str, List[float]],
        hypothesis: Dict[str, Any],
    ) -> AnalysisResults:
        """Analyze data in relation to a hypothesis.
        
        Args:
            data: Dictionary mapping variable names to lists of values
            hypothesis: Hypothesis being tested
            
        Returns:
            AnalysisResults with comprehensive statistical analysis
        """
        hyp_id = hypothesis.get("id", "unknown")
        
        # Descriptive statistics
        descriptive = self._compute_descriptive_statistics(data)
        
        # Check assumptions
        assumptions = self._check_assumptions(data)
        
        # Select and perform appropriate tests
        tests = self._perform_statistical_tests(data, hypothesis)
        
        # Calculate effect sizes
        effect_sizes = self._calculate_effect_sizes(data, tests)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            data, tests, effect_sizes, assumptions
        )
        
        # Formulate conclusion
        conclusion = self._formulate_conclusion(tests, effect_sizes, hypothesis)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(tests, effect_sizes)
        
        results = AnalysisResults(
            hypothesis_id=hyp_id,
            descriptive_stats=descriptive,
            statistical_tests=tests,
            effect_sizes=effect_sizes,
            assumptions_checks=assumptions,
            recommendations=recommendations,
            conclusion=conclusion,
            confidence_level=confidence,
        )
        
        self._analyses[hyp_id] = results
        return results
    
    def _compute_descriptive_statistics(
        self, data: Dict[str, List[float]]
    ) -> Dict[str, Dict[str, float]]:
        """Compute descriptive statistics for each variable."""
        stats = {}
        
        for var_name, values in data.items():
            if not values:
                continue
            
            var_stats = {
                "n": len(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "mode": self._calculate_mode(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0.0,
                "variance": statistics.variance(values) if len(values) > 1 else 0.0,
                "min": min(values),
                "max": max(values),
                "range": max(values) - min(values),
                "q1": self._calculate_percentile(values, 25),
                "q3": self._calculate_percentile(values, 75),
                "iqr": (self._calculate_percentile(values, 75) - 
                       self._calculate_percentile(values, 25)),
                "skewness": self._calculate_skewness(values),
                "kurtosis": self._calculate_kurtosis(values),
                "cv": (statistics.stdev(values) / statistics.mean(values) * 100
                      if len(values) > 1 and statistics.mean(values) != 0 else 0),
            }
            stats[var_name] = var_stats
        
        return stats
    
    def _calculate_mode(self, values: List[float]) -> float:
        """Calculate mode of values."""
        if not values:
            return 0.0
        
        # Round to handle continuous values
        rounded = [round(v, 2) for v in values]
        counts = {}
        for v in rounded:
            counts[v] = counts.get(v, 0) + 1
        
        return max(counts, key=counts.get)
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        index = (percentile / 100) * (n - 1)
        lower = int(index)
        upper = lower + 1
        
        if upper >= n:
            return sorted_vals[-1]
        
        weight = index - lower
        return sorted_vals[lower] * (1 - weight) + sorted_vals[upper] * weight
    
    def _calculate_skewness(self, values: List[float]) -> float:
        """Calculate skewness."""
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
        """Calculate kurtosis."""
        n = len(values)
        if n < 4:
            return 0.0
        
        mean = statistics.mean(values)
        std = statistics.stdev(values)
        
        if std == 0:
            return 0.0
        
        kurtosis = sum(((x - mean) / std) ** 4 for x in values) / n - 3
        return round(kurtosis, 4)
    
    def _check_assumptions(self, data: Dict[str, List[float]]) -> Dict[str, bool]:
        """Check statistical assumptions."""
        assumptions = {}
        
        for var_name, values in data.items():
            if len(values) < 8:
                assumptions[f"{var_name}_normality"] = False
                continue
            
            # Simple normality check using skewness and kurtosis
            skew = abs(self._calculate_skewness(values))
            kurt = abs(self._calculate_kurtosis(values))
            
            assumptions[f"{var_name}_normality"] = skew < 2 and kurt < 7
            assumptions[f"{var_name}_outliers"] = self._check_outliers(values)
            assumptions[f"{var_name}_homogeneity"] = True  # Placeholder
        
        # Check independence (simplified)
        assumptions["independence"] = True
        
        return assumptions
    
    def _check_outliers(self, values: List[float]) -> bool:
        """Check for outliers using IQR method."""
        if len(values) < 4:
            return True
        
        q1 = self._calculate_percentile(values, 25)
        q3 = self._calculate_percentile(values, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = sum(1 for v in values if v < lower_bound or v > upper_bound)
        return outliers == 0
    
    def _perform_statistical_tests(
        self, data: Dict[str, List[float]], hypothesis: Dict[str, Any]
    ) -> List[StatisticalTest]:
        """Perform appropriate statistical tests."""
        tests = []
        hyp_type = hypothesis.get("type", "correlational")
        
        var_names = list(data.keys())
        
        if len(var_names) >= 2 and hyp_type == "correlational":
            # Correlation test
            test = self._pearson_correlation(data[var_names[0]], data[var_names[1]])
            tests.append(test)
        
        if len(var_names) >= 2 and hyp_type == "causal":
            # Independent t-test (assuming two groups)
            test = self._independent_t_test(data[var_names[0]], data[var_names[1]])
            tests.append(test)
        
        if len(var_names) == 1:
            # One-sample t-test against hypothesized mean
            test = self._one_sample_t_test(data[var_names[0]], 0)
            tests.append(test)
        
        # Add regression if multiple predictors
        if len(var_names) >= 3:
            test = self._simple_linear_regression(
                data[var_names[0]], data[var_names[1]]
            )
            tests.append(test)
        
        return tests
    
    def _pearson_correlation(
        self, x: List[float], y: List[float]
    ) -> StatisticalTest:
        """Calculate Pearson correlation."""
        n = len(x)
        if n < 3:
            return StatisticalTest(
                test_type=TestType.CORRELATION_PEARSON,
                test_name="Pearson Correlation",
                statistic=0.0,
                p_value=1.0,
                effect_size=0.0,
                confidence_interval=(-1.0, 1.0),
                degrees_of_freedom=n - 2,
                interpretation="Insufficient data for correlation analysis",
                significant=False,
                assumptions_met=False,
            )
        
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        std_x = statistics.stdev(x)
        std_y = statistics.stdev(y)
        
        if std_x == 0 or std_y == 0:
            r = 0.0
        else:
            r = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / ((n - 1) * std_x * std_y)
        
        # t-statistic for correlation
        if abs(r) < 1:
            t_stat = r * math.sqrt((n - 2) / (1 - r**2))
        else:
            t_stat = float('inf')
        
        # Approximate p-value (two-tailed)
        p_value = self._approximate_t_p_value(abs(t_stat), n - 2)
        
        # Effect size is r itself
        effect_size = abs(r)
        
        # Confidence interval for r (Fisher z-transformation)
        z = 0.5 * math.log((1 + r) / (1 - r)) if abs(r) < 1 else float('inf')
        se = 1 / math.sqrt(n - 3) if n > 3 else 1
        z_lower = z - 1.96 * se
        z_upper = z + 1.96 * se
        ci_lower = math.tanh(z_lower)
        ci_upper = math.tanh(z_upper)
        
        interpretation = self._interpret_correlation(r)
        significant = p_value < self.ALPHA
        
        return StatisticalTest(
            test_type=TestType.CORRELATION_PEARSON,
            test_name="Pearson Correlation",
            statistic=round(r, 4),
            p_value=round(p_value, 6),
            effect_size=round(effect_size, 4),
            confidence_interval=(round(ci_lower, 4), round(ci_upper, 4)),
            degrees_of_freedom=n - 2,
            interpretation=interpretation,
            significant=significant,
            assumptions_met=True,
        )
    
    def _independent_t_test(
        self, group1: List[float], group2: List[float]
    ) -> StatisticalTest:
        """Perform independent samples t-test."""
        n1, n2 = len(group1), len(group2)
        
        if n1 < 2 or n2 < 2:
            return StatisticalTest(
                test_type=TestType.T_TEST_INDEPENDENT,
                test_name="Independent Samples t-test",
                statistic=0.0,
                p_value=1.0,
                effect_size=0.0,
                confidence_interval=(-1.0, 1.0),
                degrees_of_freedom=n1 + n2 - 2,
                interpretation="Insufficient sample size",
                significant=False,
                assumptions_met=False,
            )
        
        mean1 = statistics.mean(group1)
        mean2 = statistics.mean(group2)
        var1 = statistics.variance(group1)
        var2 = statistics.variance(group2)
        
        # Pooled standard error
        se = math.sqrt(var1/n1 + var2/n2)
        
        if se == 0:
            t_stat = 0.0
        else:
            t_stat = (mean1 - mean2) / se
        
        df = n1 + n2 - 2
        p_value = self._approximate_t_p_value(abs(t_stat), df)
        
        # Cohen's d
        pooled_std = math.sqrt(((n1-1)*var1 + (n2-1)*var2) / df) if df > 0 else 1
        effect_size = abs(mean1 - mean2) / pooled_std if pooled_std > 0 else 0
        
        # Confidence interval
        ci_margin = 1.96 * se
        ci_lower = (mean1 - mean2) - ci_margin
        ci_upper = (mean1 - mean2) + ci_margin
        
        interpretation = self._interpret_t_test(t_stat, p_value, effect_size)
        significant = p_value < self.ALPHA
        
        return StatisticalTest(
            test_type=TestType.T_TEST_INDEPENDENT,
            test_name="Independent Samples t-test",
            statistic=round(t_stat, 4),
            p_value=round(p_value, 6),
            effect_size=round(effect_size, 4),
            confidence_interval=(round(ci_lower, 4), round(ci_upper, 4)),
            degrees_of_freedom=df,
            interpretation=interpretation,
            significant=significant,
            assumptions_met=True,
        )
    
    def _one_sample_t_test(
        self, sample: List[float], hypothesized_mean: float
    ) -> StatisticalTest:
        """Perform one-sample t-test."""
        n = len(sample)
        
        if n < 2:
            return StatisticalTest(
                test_type=TestType.T_TEST_ONE_SAMPLE,
                test_name="One-sample t-test",
                statistic=0.0,
                p_value=1.0,
                effect_size=0.0,
                confidence_interval=(hypothesized_mean, hypothesized_mean),
                degrees_of_freedom=n - 1,
                interpretation="Insufficient sample size",
                significant=False,
                assumptions_met=False,
            )
        
        mean = statistics.mean(sample)
        std = statistics.stdev(sample)
        se = std / math.sqrt(n)
        
        if se == 0:
            t_stat = 0.0
        else:
            t_stat = (mean - hypothesized_mean) / se
        
        df = n - 1
        p_value = self._approximate_t_p_value(abs(t_stat), df)
        
        # Cohen's d
        effect_size = abs(mean - hypothesized_mean) / std if std > 0 else 0
        
        # Confidence interval
        ci_margin = 1.96 * se
        ci_lower = mean - ci_margin
        ci_upper = mean + ci_margin
        
        interpretation = f"Sample mean ({mean:.3f}) {'differs significantly' if p_value < self.ALPHA else 'does not differ significantly'} from hypothesized value ({hypothesized_mean})"
        significant = p_value < self.ALPHA
        
        return StatisticalTest(
            test_type=TestType.T_TEST_ONE_SAMPLE,
            test_name="One-sample t-test",
            statistic=round(t_stat, 4),
            p_value=round(p_value, 6),
            effect_size=round(effect_size, 4),
            confidence_interval=(round(ci_lower, 4), round(ci_upper, 4)),
            degrees_of_freedom=df,
            interpretation=interpretation,
            significant=significant,
            assumptions_met=True,
        )
    
    def _simple_linear_regression(
        self, x: List[float], y: List[float]
    ) -> StatisticalTest:
        """Perform simple linear regression."""
        n = len(x)
        
        if n < 3:
            return StatisticalTest(
                test_type=TestType.REGRESSION_LINEAR,
                test_name="Simple Linear Regression",
                statistic=0.0,
                p_value=1.0,
                effect_size=0.0,
                confidence_interval=(0.0, 0.0),
                degrees_of_freedom=n - 2,
                interpretation="Insufficient data for regression",
                significant=False,
                assumptions_met=False,
            )
        
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        
        ss_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        ss_xx = sum((xi - mean_x) ** 2 for xi in x)
        
        if ss_xx == 0:
            slope = 0.0
        else:
            slope = ss_xy / ss_xx
        
        intercept = mean_y - slope * mean_x
        
        # R-squared
        y_pred = [slope * xi + intercept for xi in x]
        ss_res = sum((yi - yp) ** 2 for yi, yp in zip(y, y_pred))
        ss_tot = sum((yi - mean_y) ** 2 for yi in y)
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # F-statistic
        ms_reg = ss_xy ** 2 / ss_xx if ss_xx > 0 else 0
        ms_res = ss_res / (n - 2) if n > 2 else 1
        f_stat = ms_reg / ms_res if ms_res > 0 else 0
        
        p_value = self._approximate_f_p_value(f_stat, 1, n - 2)
        
        interpretation = (
            f"Regression model explains {r_squared*100:.1f}% of variance. "
            f"Slope: {slope:.4f}"
        )
        significant = p_value < self.ALPHA
        
        return StatisticalTest(
            test_type=TestType.REGRESSION_LINEAR,
            test_name="Simple Linear Regression",
            statistic=round(f_stat, 4),
            p_value=round(p_value, 6),
            effect_size=round(math.sqrt(r_squared), 4),
            confidence_interval=(round(slope - 1.96 * math.sqrt(ms_res/ss_xx), 4),
                               round(slope + 1.96 * math.sqrt(ms_res/ss_xx), 4)),
            degrees_of_freedom=n - 2,
            interpretation=interpretation,
            significant=significant,
            assumptions_met=True,
        )
    
    def _approximate_t_p_value(self, t: float, df: int) -> float:
        """Approximate p-value from t-distribution."""
        if df <= 0:
            return 1.0
        
        # Simple approximation using normal for large df
        if df > 30:
            # Use normal approximation
            z = t
            return 2 * (1 - self._normal_cdf(z))
        
        # Approximation for smaller df
        x = df / (df + t ** 2)
        p = 0.5 * self._incomplete_beta(df / 2, 0.5, x)
        
        return min(max(2 * p, 0.0), 1.0)
    
    def _approximate_f_p_value(self, f: float, df1: int, df2: int) -> float:
        """Approximate p-value from F-distribution."""
        if df1 <= 0 or df2 <= 0:
            return 1.0
        
        # Simple approximation
        x = df2 / (df2 + df1 * f)
        p = self._incomplete_beta(df2 / 2, df1 / 2, x)
        
        return min(max(p, 0.0), 1.0)
    
    def _normal_cdf(self, x: float) -> float:
        """Approximate normal CDF."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    def _incomplete_beta(self, a: float, b: float, x: float) -> float:
        """Approximate incomplete beta function."""
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        
        # Simple numerical integration
        n = 100
        dx = x / n
        total = 0
        
        for i in range(n):
            xi = (i + 0.5) * dx
            if xi > 0 and xi < 1:
                total += xi ** (a - 1) * (1 - xi) ** (b - 1) * dx
        
        # Normalize by beta function
        beta = self._beta_function(a, b)
        
        return total / beta if beta > 0 else 0.5
    
    def _beta_function(self, a: float, b: float) -> float:
        """Approximate beta function using gamma."""
        return math.gamma(a) * math.gamma(b) / math.gamma(a + b)
    
    def _interpret_correlation(self, r: float) -> str:
        """Interpret correlation coefficient."""
        abs_r = abs(r)
        direction = "positive" if r > 0 else "negative"
        
        if abs_r >= 0.9:
            strength = "very strong"
        elif abs_r >= 0.7:
            strength = "strong"
        elif abs_r >= 0.5:
            strength = "moderate"
        elif abs_r >= 0.3:
            strength = "weak"
        else:
            strength = "negligible"
        
        return f"{strength} {direction} correlation (r = {r:.4f})"
    
    def _interpret_t_test(
        self, t: float, p: float, d: float
    ) -> str:
        """Interpret t-test results."""
        sig = "statistically significant" if p < self.ALPHA else "not statistically significant"
        
        if d >= 0.8:
            effect = "large"
        elif d >= 0.5:
            effect = "medium"
        elif d >= 0.2:
            effect = "small"
        else:
            effect = "negligible"
        
        return f"Result is {sig} (p = {p:.4f}) with {effect} effect size (d = {d:.4f})"
    
    def _calculate_effect_sizes(
        self, data: Dict[str, List[float]], tests: List[StatisticalTest]
    ) -> Dict[str, float]:
        """Calculate effect sizes for all comparisons."""
        effect_sizes = {}
        
        for test in tests:
            effect_sizes[test.test_name] = test.effect_size
        
        # Additional effect sizes
        var_names = list(data.keys())
        if len(var_names) >= 2:
            # Cohen's d between first two variables
            effect_sizes["cohens_d"] = self._calculate_cohens_d(
                data[var_names[0]], data[var_names[1]]
            )
        
        return effect_sizes
    
    def _calculate_cohens_d(self, group1: List[float], group2: List[float]) -> float:
        """Calculate Cohen's d effect size."""
        n1, n2 = len(group1), len(group2)
        
        if n1 < 2 or n2 < 2:
            return 0.0
        
        mean1 = statistics.mean(group1)
        mean2 = statistics.mean(group2)
        var1 = statistics.variance(group1)
        var2 = statistics.variance(group2)
        
        pooled_std = math.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1 + n2 - 2))
        
        if pooled_std == 0:
            return 0.0
        
        return abs(mean1 - mean2) / pooled_std
    
    def _generate_recommendations(
        self,
        data: Dict[str, List[float]],
        tests: List[StatisticalTest],
        effect_sizes: Dict[str, float],
        assumptions: Dict[str, bool],
    ) -> List[str]:
        """Generate analysis recommendations."""
        recommendations = []
        
        # Check sample size
        for var_name, values in data.items():
            if len(values) < 30:
                recommendations.append(
                    f"Consider increasing sample size for {var_name} (currently n={len(values)})"
                )
        
        # Check assumptions
        for assumption, met in assumptions.items():
            if not met and "normality" in assumption:
                recommendations.append(
                    f"Normality assumption violated for {assumption.split('_')[0]}. "
                    "Consider non-parametric alternatives."
                )
        
        # Check effect sizes
        for name, size in effect_sizes.items():
            if size < 0.2:
                recommendations.append(
                    f"Small effect size detected for {name}. "
                    "Consider practical significance alongside statistical significance."
                )
        
        # Check power
        recommendations.append("Consider conducting power analysis for future studies")
        
        return recommendations[:5]
    
    def _formulate_conclusion(
        self,
        tests: List[StatisticalTest],
        effect_sizes: Dict[str, float],
        hypothesis: Dict[str, Any],
    ) -> str:
        """Formulate conclusion based on results."""
        if not tests:
            return "No statistical tests were performed."
        
        significant_tests = [t for t in tests if t.significant]
        total_tests = len(tests)
        
        if len(significant_tests) == total_tests:
            strength = "strong"
        elif len(significant_tests) > total_tests / 2:
            strength = "moderate"
        elif len(significant_tests) > 0:
            strength = "weak"
        else:
            strength = "no"
        
        hyp_statement = hypothesis.get("statement", "the hypothesis")
        
        conclusion = (
            f"The analysis provides {strength} statistical support for {hyp_statement[:100]}. "
            f"{len(significant_tests)}/{total_tests} statistical tests reached significance "
            f"at α = {self.ALPHA}."
        )
        
        return conclusion
    
    def _calculate_confidence(
        self, tests: List[StatisticalTest], effect_sizes: Dict[str, float]
    ) -> float:
        """Calculate overall confidence level."""
        if not tests:
            return 0.0
        
        # Base confidence from significant tests
        sig_ratio = sum(1 for t in tests if t.significant) / len(tests)
        
        # Effect size contribution
        avg_effect = statistics.mean(effect_sizes.values()) if effect_sizes else 0
        
        # Combined confidence
        confidence = sig_ratio * 0.6 + avg_effect * 0.4
        
        return min(max(confidence, 0.0), 1.0)
