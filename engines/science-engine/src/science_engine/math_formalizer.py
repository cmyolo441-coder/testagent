"""Math Formalizer - Converts scientific theories into mathematical formalizations."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass
class MathematicalFormalization:
    """Mathematical formalization of a theory."""
    theory_id: str
    equations: List[str]
    variables: Dict[str, str]  # variable_name -> description
    constraints: List[str]
    axioms: List[str]
    notation: Dict[str, str]  # symbol -> meaning
    dimensional_analysis: Dict[str, str]  # variable -> dimensions
    assumptions: List[str]
    formal_language: str
    latex_representation: str
    complexity_score: float
    completeness_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "theory_id": self.theory_id,
            "equations": self.equations,
            "variables": self.variables,
            "constraints": self.constraints,
            "axioms": self.axioms,
            "notation": self.notation,
            "dimensional_analysis": self.dimensional_analysis,
            "assumptions": self.assumptions,
            "formal_language": self.formal_language,
            "latex_representation": self.latex_representation,
            "complexity_score": self.complexity_score,
            "completeness_score": self.completeness_score,
        }


class MathFormalizer:
    """Converts scientific theories into mathematical formalizations.
    
    Translates qualitative scientific theories into precise mathematical
    representations suitable for computational analysis and verification.
    """
    
    # Common mathematical operators and their LaTeX equivalents
    OPERATORS = {
        "forall": "\\forall",
        "exists": "\\exists",
        "implies": "\\Rightarrow",
        "iff": "\\Leftrightarrow",
        "and": "\\wedge",
        "or": "\\vee",
        "not": "\\neg",
        "subset": "\\subset",
        "element": "\\in",
        "union": "\\cup",
        "intersection": "\\cap",
    }
    
    def __init__(self):
        self._formalizations: Dict[str, MathematicalFormalization] = {}
        self._variable_counter = 0
    
    def formalize(self, theory: Dict[str, Any]) -> MathematicalFormalization:
        """Formalize a scientific theory into mathematical representation.
        
        Args:
            theory: Dictionary containing theory information
            
        Returns:
            MathematicalFormalization with equations and formal structure
        """
        theory_id = theory.get("id", "unknown")
        
        # Extract components from theory
        hypotheses = theory.get("hypotheses", [])
        predictions = theory.get("predictions", [])
        assumptions = theory.get("assumptions", [])
        scope = theory.get("scope", "")
        
        # Generate mathematical components
        variables = self._extract_variables(hypotheses)
        equations = self._generate_equations(hypotheses, variables)
        constraints = self._generate_constraints(hypotheses, variables)
        axioms = self._generate_axioms(assumptions, scope)
        notation = self._generate_notation(variables)
        dimensional_analysis = self._perform_dimensional_analysis(variables)
        
        # Generate formal language representation
        formal_language = self._generate_formal_language(
            equations, variables, constraints
        )
        
        # Generate LaTeX
        latex = self._generate_latex(equations, variables, notation)
        
        # Calculate metrics
        complexity = self._calculate_complexity(equations, variables)
        completeness = self._calculate_completeness(
            hypotheses, equations, predictions
        )
        
        formalization = MathematicalFormalization(
            theory_id=theory_id,
            equations=equations,
            variables=variables,
            constraints=constraints,
            axioms=axioms,
            notation=notation,
            dimensional_analysis=dimensional_analysis,
            assumptions=assumptions,
            formal_language=formal_language,
            latex_representation=latex,
            complexity_score=complexity,
            completeness_score=completeness,
        )
        
        self._formalizations[theory_id] = formalization
        return formalization
    
    def _extract_variables(self, hypotheses: List[Dict[str, Any]]) -> Dict[str, str]:
        """Extract and classify variables from hypotheses."""
        variables = {}
        
        for hyp in hypotheses:
            hyp_variables = hyp.get("variables", [])
            hyp_type = hyp.get("type", "correlational")
            
            for var in hyp_variables:
                if var not in variables:
                    self._variable_counter += 1
                    # Classify variable based on context
                    if hyp_type == "causal":
                        if self._variable_counter % 2 == 0:
                            variables[var] = "independent_variable"
                        else:
                            variables[var] = "dependent_variable"
                    elif hyp_type == "predictive":
                        variables[var] = "predictor" if self._variable_counter % 2 == 0 else "outcome"
                    else:
                        variables[var] = "observed_variable"
        
        # Add derived variables
        var_names = list(variables.keys())
        if len(var_names) >= 2:
            variables[f"Δ{var_names[0]}"] = "change_in_variable"
            variables[f"Σ{var_names[0]}"] = "summation_variable"
        
        return variables
    
    def _generate_equations(
        self, hypotheses: List[Dict[str, Any]], variables: Dict[str, str]
    ) -> List[str]:
        """Generate mathematical equations from hypotheses."""
        equations = []
        
        for i, hyp in enumerate(hypotheses):
            hyp_type = hyp.get("type", "correlational")
            hyp_vars = hyp.get("variables", [])
            
            if not hyp_vars:
                continue
            
            if hyp_type == "causal":
                if len(hyp_vars) >= 2:
                    equations.append(
                        f"{hyp_vars[1]} = f({hyp_vars[0]}) + ε, where ε ~ N(0, σ²)"
                    )
                    equations.append(
                        f"∂{hyp_vars[1]}/∂{hyp_vars[0]} > 0  (positive causal effect)"
                    )
            elif hyp_type == "correlational":
                if len(hyp_vars) >= 2:
                    equations.append(
                        f"ρ({hyp_vars[0]}, {hyp_vars[1]}) = "
                        f"Cov({hyp_vars[0]}, {hyp_vars[1]}) / (σ_{hyp_vars[0]} * σ_{hyp_vars[1]})"
                    )
            elif hyp_type == "predictive":
                if len(hyp_vars) >= 2:
                    equations.append(
                        f"E[{hyp_vars[1]} | {hyp_vars[0]}] = β₀ + β₁ * {hyp_vars[0]}"
                    )
            elif hyp_type == "explanatory":
                equations.append(
                    f"Mechanism({hyp_vars[0] if hyp_vars else 'X'}) → Observable_consequence"
                )
        
        # Add general system equation
        if variables:
            var_list = list(variables.keys())[:5]
            equations.append(
                f"System: d/dt [{', '.join(var_list)}] = F([{', '.join(var_list)}], t)"
            )
        
        return equations
    
    def _generate_constraints(
        self, hypotheses: List[Dict[str, Any]], variables: Dict[str, str]
    ) -> List[str]:
        """Generate mathematical constraints."""
        constraints = []
        
        # Physical constraints
        constraints.append("All variables are real-valued: x ∈ ℝ")
        constraints.append("Probability constraints: 0 ≤ P(E) ≤ 1 for all events E")
        
        # Variable-specific constraints
        for var in variables:
            if "probability" in variables[var].lower():
                constraints.append(f"0 ≤ {var} ≤ 1")
            elif "count" in variables[var].lower():
                constraints.append(f"{var} ∈ ℤ≥0")
            elif "time" in var.lower():
                constraints.append(f"{var} ≥ 0")
        
        # Constraint from hypotheses
        for hyp in hypotheses:
            if hyp.get("type") == "causal":
                hyp_vars = hyp.get("variables", [])
                if len(hyp_vars) >= 2:
                    constraints.append(
                        f"∂{hyp_vars[1]}/∂{hyp_vars[0]} is well-defined and finite"
                    )
        
        return constraints
    
    def _generate_axioms(self, assumptions: List[str], scope: str) -> List[str]:
        """Generate axioms from assumptions."""
        axioms = []
        
        # Core scientific axioms
        axioms.append("Axiom 1: The universe is comprehensible through mathematics")
        axioms.append("Axiom 2: Causal relationships are transitive in time")
        axioms.append("Axiom 3: Measurements are reproducible under identical conditions")
        
        # Assumption-derived axioms
        for i, assumption in enumerate(assumptions[:5], 4):
            axioms.append(f"Axiom {i}: {assumption}")
        
        # Domain-specific axioms
        if "physical" in scope.lower():
            axioms.append("Axiom: Conservation laws hold for closed systems")
        if "biological" in scope.lower():
            axioms.append("Axiom: Biological systems are subject to natural selection")
        if "social" in scope.lower():
            axioms.append("Axiom: Individual behavior is influenced by social context")
        
        return axioms
    
    def _generate_notation(self, variables: Dict[str, str]) -> Dict[str, str]:
        """Generate mathematical notation."""
        notation = {
            "ℝ": "Real numbers",
            "ℕ": "Natural numbers",
            "ℤ": "Integers",
            "ℂ": "Complex numbers",
            "∀": "For all",
            "∃": "There exists",
            "→": "Maps to / implies",
            "⇒": "Implies",
            "⇔": "If and only if",
            "∈": "Element of",
            "⊆": "Subset of",
            "∪": "Union",
            "∩": "Intersection",
            "∑": "Summation",
            "∫": "Integral",
            "∂": "Partial derivative",
            "Δ": "Change in",
        }
        
        # Add variable-specific notation
        for var in variables:
            if var not in notation:
                notation[var] = variables[var]
        
        return notation
    
    def _perform_dimensional_analysis(self, variables: Dict[str, str]) -> Dict[str, str]:
        """Perform dimensional analysis on variables."""
        dimensions = {}
        
        dimension_map = {
            "time": "T",
            "length": "L",
            "mass": "M",
            "temperature": "Θ",
            "current": "I",
            "amount": "N",
            "luminosity": "J",
        }
        
        for var, var_type in variables.items():
            var_lower = var.lower()
            
            if "time" in var_lower or "duration" in var_lower:
                dimensions[var] = "T"
            elif "length" in var_lower or "distance" in var_lower or "position" in var_lower:
                dimensions[var] = "L"
            elif "mass" in var_lower or "weight" in var_lower:
                dimensions[var] = "M"
            elif "velocity" in var_lower or "speed" in var_lower:
                dimensions[var] = "L·T⁻¹"
            elif "acceleration" in var_lower:
                dimensions[var] = "L·T⁻²"
            elif "force" in var_lower:
                dimensions[var] = "M·L·T⁻²"
            elif "energy" in var_lower or "work" in var_lower:
                dimensions[var] = "M·L²·T⁻²"
            elif "probability" in var_lower:
                dimensions[var] = "1 (dimensionless)"
            elif "count" in var_lower or "number" in var_lower:
                dimensions[var] = "N"
            else:
                dimensions[var] = "Depends on context"
        
        return dimensions
    
    def _generate_formal_language(
        self,
        equations: List[str],
        variables: Dict[str, str],
        constraints: List[str],
    ) -> str:
        """Generate formal language representation."""
        lines = []
        lines.append("FORMAL SPECIFICATION")
        lines.append("=" * 50)
        
        # Variables declaration
        lines.append("\nVARIABLES:")
        for var, desc in variables.items():
            lines.append(f"  {var}: {desc}")
        
        # Axioms
        lines.append("\nAXIOMS:")
        lines.append("  ∀x ∈ Domain: Consistent(x)")
        
        # Equations
        lines.append("\nEQUATIONS:")
        for eq in equations:
            lines.append(f"  {eq}")
        
        # Constraints
        lines.append("\nCONSTRAINTS:")
        for constraint in constraints[:5]:
            lines.append(f"  {constraint}")
        
        # Properties
        lines.append("\nPROPERTIES:")
        lines.append("  ∀t: Consistent(System(t))")
        lines.append("  ∀e: Observable(e) ⇒ Explainable(e, Theory)")
        
        return "\n".join(lines)
    
    def _generate_latex(
        self,
        equations: List[str],
        variables: Dict[str, str],
        notation: Dict[str, str],
    ) -> str:
        """Generate LaTeX representation."""
        latex_lines = []
        latex_lines.append("\\documentclass{article}")
        latex_lines.append("\\usepackage{amsmath}")
        latex_lines.append("\\begin{document}")
        latex_lines.append("\\section{Mathematical Formalization}")
        
        # Variables
        latex_lines.append("\\subsection{Variables}")
        latex_lines.append("\\begin{itemize}")
        for var in list(variables.keys())[:10]:
            escaped_var = var.replace("_", "\\_").replace("{", "\\{").replace("}", "\\}")
            latex_lines.append(f"  \\item ${escaped_var}$: {variables[var]}")
        latex_lines.append("\\end{itemize}")
        
        # Equations
        latex_lines.append("\\subsection{Equations}")
        for i, eq in enumerate(equations[:5], 1):
            # Simple LaTeX escaping
            latex_eq = eq.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
            latex_lines.append(f"Equation {i}: \\verb|{latex_eq}|")
        
        latex_lines.append("\\end{document}")
        
        return "\n".join(latex_lines)
    
    def _calculate_complexity(
        self, equations: List[str], variables: Dict[str, str]
    ) -> float:
        """Calculate complexity score."""
        # Base complexity from number of equations
        equation_complexity = min(len(equations) * 0.1, 0.4)
        
        # Variable complexity
        variable_complexity = min(len(variables) * 0.05, 0.3)
        
        # Symbolic complexity (count operators and functions)
        symbol_count = 0
        for eq in equations:
            symbol_count += eq.count("+") + eq.count("-") + eq.count("*")
            symbol_count += eq.count("∫") + eq.count("∑") + eq.count("∂")
        
        symbolic_complexity = min(symbol_count * 0.02, 0.3)
        
        return min(equation_complexity + variable_complexity + symbolic_complexity, 1.0)
    
    def _calculate_completeness(
        self,
        hypotheses: List[Dict[str, Any]],
        equations: List[str],
        predictions: List[str],
    ) -> float:
        """Calculate completeness score."""
        if not hypotheses:
            return 0.0
        
        # Coverage of hypotheses
        hyp_with_vars = sum(1 for h in hypotheses if h.get("variables"))
        hyp_coverage = hyp_with_vars / len(hypotheses)
        
        # Equation coverage
        equation_coverage = min(len(equations) / max(len(hypotheses), 1), 1.0)
        
        # Prediction formalization
        prediction_coverage = min(len(predictions) * 0.1, 0.3)
        
        return (hyp_coverage * 0.4 + equation_coverage * 0.4 + prediction_coverage * 0.2)
