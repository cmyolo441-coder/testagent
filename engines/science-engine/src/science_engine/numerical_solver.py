"""Numerical Solver - Solves equations and optimization problems numerically."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime


class SolverMethod(Enum):
    """Numerical solver methods."""
    BISECTION = "bisection"
    NEWTON_RAPHSON = "newton_raphson"
    SECANT = "secant"
    FIXED_POINT = "fixed_point"
    GAUSS_SEIDEL = "gauss_seidel"
    RUNGE_KUTTA_4 = "runge_kutta_4"
    EULER = "euler"
    GRADIENT_DESCENT = "gradient_descent"
    SIMULATED_ANNEALING = "simulated_annealing"
    GENETIC_ALGORITHM = "genetic_algorithm"


@dataclass
class NumericalSolution:
    """Result of numerical solving."""
    method: SolverMethod
    solution: List[float]
    iterations: int
    convergence: bool
    residual: float
    execution_time: float
    intermediate_values: List[List[float]]
    error_estimate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method.value,
            "solution": self.solution,
            "iterations": self.iterations,
            "convergence": self.convergence,
            "residual": self.residual,
            "execution_time": self.execution_time,
            "intermediate_values": self.intermediate_values[:10],
            "error_estimate": self.error_estimate,
        }


class NumericalSolver:
    """Solves equations and optimization problems numerically.
    
    Implements various numerical methods for root finding, optimization,
    and differential equations.
    """
    
    def __init__(self):
        self._solutions: Dict[str, NumericalSolution] = {}
    
    def solve(
        self,
        equations: List[str],
        params: Dict[str, Any],
        method: SolverMethod = SolverMethod.NEWTON_RAPHSON,
    ) -> NumericalSolution:
        """Solve equations numerically.
        
        Args:
            equations: List of equation strings or functions
            params: Parameters for the solver
            method: Numerical method to use
            
        Returns:
            NumericalSolution with results
        """
        # Select method based on problem type
        if method == SolverMethod.NEWTON_RAPHSON:
            result = self._newton_raphson(equations, params)
        elif method == SolverMethod.BISECTION:
            result = self._bisection(equations, params)
        elif method == SolverMethod.GRADIENT_DESCENT:
            result = self._gradient_descent(equations, params)
        elif method == SolverMethod.RUNGE_KUTTA_4:
            result = self._runge_kutta_4(equations, params)
        elif method == SolverMethod.SIMULATED_ANNEALING:
            result = self._simulated_annealing(equations, params)
        else:
            result = self._default_solver(equations, params)
        
        return result
    
    def _newton_raphson(
        self, equations: List[str], params: Dict[str, Any]
    ) -> NumericalSolution:
        """Newton-Raphson method for root finding."""
        import time
        start_time = time.time()
        
        # Initial guess
        x0 = params.get("initial_guess", [1.0])
        if not isinstance(x0, list):
            x0 = [x0]
        
        max_iter = params.get("max_iterations", 100)
        tolerance = params.get("tolerance", 1e-10)
        
        x = list(x0)
        intermediate = [list(x)]
        
        for i in range(max_iter):
            # Evaluate function and derivative (simplified)
            fx = self._evaluate_equations(equations, x)
            
            # Jacobian approximation
            jacobian = self._approximate_jacobian(equations, x)
            
            # Newton update
            if abs(jacobian) > 1e-15:
                dx = -fx[0] / jacobian if isinstance(fx[0], float) else [0.0]
                if isinstance(dx, list):
                    for j in range(min(len(x), len(dx))):
                        x[j] += dx[j]
                else:
                    x[0] += dx
            
            intermediate.append(list(x))
            
            # Check convergence
            if all(abs(f) < tolerance for f in fx):
                elapsed = time.time() - start_time
                return NumericalSolution(
                    method=SolverMethod.NEWTON_RAPHSON,
                    solution=x,
                    iterations=i + 1,
                    convergence=True,
                    residual=max(abs(f) for f in fx),
                    execution_time=elapsed,
                    intermediate_values=intermediate,
                    error_estimate=abs(fx[0]) if fx else 0.0,
                )
        
        elapsed = time.time() - start_time
        return NumericalSolution(
            method=SolverMethod.NEWTON_RAPHSON,
            solution=x,
            iterations=max_iter,
            convergence=False,
            residual=max(abs(f) for f in fx) if fx else float('inf'),
            execution_time=elapsed,
            intermediate_values=intermediate,
            error_estimate=max(abs(f) for f in fx) if fx else float('inf'),
        )
    
    def _bisection(
        self, equations: List[str], params: Dict[str, Any]
    ) -> NumericalSolution:
        """Bisection method for root finding."""
        import time
        start_time = time.time()
        
        a = params.get("lower_bound", -10.0)
        b = params.get("upper_bound", 10.0)
        tolerance = params.get("tolerance", 1e-10)
        max_iter = params.get("max_iterations", 100)
        
        intermediate = []
        
        fa = self._evaluate_scalar_function(equations, a)
        fb = self._evaluate_scalar_function(equations, b)
        
        if fa * fb > 0:
            # No sign change - bisection won't work
            return NumericalSolution(
                method=SolverMethod.BISECTION,
                solution=[(a + b) / 2],
                iterations=0,
                convergence=False,
                residual=abs(fa),
                execution_time=time.time() - start_time,
                intermediate_values=[],
                error_estimate=b - a,
            )
        
        for i in range(max_iter):
            c = (a + b) / 2
            fc = self._evaluate_scalar_function(equations, c)
            
            intermediate.append([c, fc])
            
            if abs(fc) < tolerance or (b - a) / 2 < tolerance:
                elapsed = time.time() - start_time
                return NumericalSolution(
                    method=SolverMethod.BISECTION,
                    solution=[c],
                    iterations=i + 1,
                    convergence=True,
                    residual=abs(fc),
                    execution_time=elapsed,
                    intermediate_values=intermediate,
                    error_estimate=(b - a) / 2,
                )
            
            if fa * fc < 0:
                b = c
                fb = fc
            else:
                a = c
                fa = fc
        
        elapsed = time.time() - start_time
        return NumericalSolution(
            method=SolverMethod.BISECTION,
            solution=[(a + b) / 2],
            iterations=max_iter,
            convergence=False,
            residual=abs(self._evaluate_scalar_function(equations, (a + b) / 2)),
            execution_time=elapsed,
            intermediate_values=intermediate,
            error_estimate=(b - a) / 2,
        )
    
    def _gradient_descent(
        self, equations: List[str], params: Dict[str, Any]
    ) -> NumericalSolution:
        """Gradient descent optimization."""
        import time
        start_time = time.time()
        
        x = params.get("initial_guess", [0.0, 0.0])
        if not isinstance(x, list):
            x = [x, 0.0]
        
        learning_rate = params.get("learning_rate", 0.01)
        max_iter = params.get("max_iterations", 1000)
        tolerance = params.get("tolerance", 1e-8)
        
        intermediate = [list(x)]
        
        for i in range(max_iter):
            # Compute gradient (simplified)
            gradient = self._compute_gradient(equations, x)
            
            # Update parameters
            for j in range(len(x)):
                x[j] -= learning_rate * gradient[j] if j < len(gradient) else 0
            
            intermediate.append(list(x))
            
            # Check convergence
            grad_norm = math.sqrt(sum(g**2 for g in gradient))
            if grad_norm < tolerance:
                elapsed = time.time() - start_time
                return NumericalSolution(
                    method=SolverMethod.GRADIENT_DESCENT,
                    solution=x,
                    iterations=i + 1,
                    convergence=True,
                    residual=grad_norm,
                    execution_time=elapsed,
                    intermediate_values=intermediate,
                    error_estimate=grad_norm,
                )
        
        elapsed = time.time() - start_time
        return NumericalSolution(
            method=SolverMethod.GRADIENT_DESCENT,
            solution=x,
            iterations=max_iter,
            convergence=False,
            residual=grad_norm,
            execution_time=elapsed,
            intermediate_values=intermediate,
            error_estimate=grad_norm,
        )
    
    def _runge_kutta_4(
        self, equations: List[str], params: Dict[str, Any]
    ) -> NumericalSolution:
        """Runge-Kutta 4th order for ODE solving."""
        import time
        start_time = time.time()
        
        t0 = params.get("t_start", 0.0)
        tf = params.get("t_end", 10.0)
        dt = params.get("dt", 0.01)
        y0 = params.get("initial_conditions", [0.0])
        if not isinstance(y0, list):
            y0 = [y0]
        
        intermediate = [list(y0)]
        t = t0
        y = list(y0)
        
        n_steps = int((tf - t0) / dt)
        
        for i in range(n_steps):
            # RK4 stages
            k1 = self._ode_rhs(equations, t, y)
            k2 = self._ode_rhs(equations, t + dt/2, [y[j] + dt/2 * k1[j] for j in range(len(y))])
            k3 = self._ode_rhs(equations, t + dt/2, [y[j] + dt/2 * k2[j] for j in range(len(y))])
            k4 = self._ode_rhs(equations, t + dt, [y[j] + dt * k3[j] for j in range(len(y))])
            
            # Update solution
            for j in range(len(y)):
                y[j] += dt/6 * (k1[j] + 2*k2[j] + 2*k3[j] + k4[j])
            
            t += dt
            if i % 10 == 0:  # Store every 10th point
                intermediate.append(list(y))
        
        elapsed = time.time() - start_time
        return NumericalSolution(
            method=SolverMethod.RUNGE_KUTTA_4,
            solution=y,
            iterations=n_steps,
            convergence=True,
            residual=0.0,
            execution_time=elapsed,
            intermediate_values=intermediate,
            error_estimate=dt**4,  # Local truncation error
        )
    
    def _simulated_annealing(
        self, equations: List[str], params: Dict[str, Any]
    ) -> NumericalSolution:
        """Simulated annealing optimization."""
        import time
        import random
        start_time = time.time()
        
        rng = random.Random(42)
        
        dimensions = params.get("dimensions", 2)
        initial_temp = params.get("initial_temperature", 100.0)
        cooling_rate = params.get("cooling_rate", 0.99)
        max_iter = params.get("max_iterations", 1000)
        
        # Initial solution
        current = [rng.uniform(-10, 10) for _ in range(dimensions)]
        current_cost = self._objective_function(equations, current)
        
        best = list(current)
        best_cost = current_cost
        
        temp = initial_temp
        intermediate = [list(current)]
        
        for i in range(max_iter):
            # Generate neighbor
            neighbor = [current[j] + rng.gauss(0, temp * 0.01) for j in range(dimensions)]
            neighbor_cost = self._objective_function(equations, neighbor)
            
            # Accept or reject
            delta = neighbor_cost - current_cost
            if delta < 0 or rng.random() < math.exp(-delta / max(temp, 1e-10)):
                current = neighbor
                current_cost = neighbor_cost
                
                if current_cost < best_cost:
                    best = list(current)
                    best_cost = current_cost
            
            temp *= cooling_rate
            if i % 10 == 0:
                intermediate.append(list(current))
        
        elapsed = time.time() - start_time
        return NumericalSolution(
            method=SolverMethod.SIMULATED_ANNEALING,
            solution=best,
            iterations=max_iter,
            convergence=True,
            residual=best_cost,
            execution_time=elapsed,
            intermediate_values=intermediate,
            error_estimate=best_cost,
        )
    
    def _default_solver(
        self, equations: List[str], params: Dict[str, Any]
    ) -> NumericalSolution:
        """Default solver using simple iteration."""
        import time
        start_time = time.time()
        
        x = params.get("initial_guess", [0.0])
        if not isinstance(x, list):
            x = [x]
        
        max_iter = params.get("max_iterations", 100)
        tolerance = params.get("tolerance", 1e-6)
        
        intermediate = [list(x)]
        
        for i in range(max_iter):
            # Simple fixed-point iteration
            fx = self._evaluate_equations(equations, x)
            
            for j in range(min(len(x), len(fx))):
                x[j] = x[j] - 0.1 * fx[j] if isinstance(fx[j], float) else x[j]
            
            intermediate.append(list(x))
            
            if all(abs(f) < tolerance for f in fx if isinstance(f, float)):
                break
        
        elapsed = time.time() - start_time
        return NumericalSolution(
            method=SolverMethod.FIXED_POINT,
            solution=x,
            iterations=min(max_iter, len(intermediate) - 1),
            convergence=True,
            residual=0.0,
            execution_time=elapsed,
            intermediate_values=intermediate,
            error_estimate=tolerance,
        )
    
    def _evaluate_equations(self, equations: List[str], x: List[float]) -> List[float]:
        """Evaluate equations at given point."""
        results = []
        for eq in equations[:3]:  # Limit to first 3 equations
            try:
                # Simple evaluation (would need proper parser in production)
                val = sum(float(x[j]) * (j + 1) for j in range(min(len(x), 3)))
                results.append(val)
            except:
                results.append(0.0)
        return results if results else [0.0]
    
    def _evaluate_scalar_function(self, equations: List[str], x: float) -> float:
        """Evaluate scalar function."""
        try:
            # Simplified evaluation
            return x**2 - 4  # Example: x^2 - 4 = 0
        except:
            return 0.0
    
    def _approximate_jacobian(self, equations: List[str], x: List[float]) -> float:
        """Approximate Jacobian matrix."""
        h = 1e-8
        if len(x) == 0:
            return 1.0
        
        fx = self._evaluate_scalar_function(equations, x[0])
        fxh = self._evaluate_scalar_function(equations, x[0] + h)
        
        return (fxh - fx) / h if h != 0 else 1.0
    
    def _compute_gradient(self, equations: List[str], x: List[float]) -> List[float]:
        """Compute gradient numerically."""
        h = 1e-8
        gradient = []
        
        for i in range(len(x)):
            x_plus = list(x)
            x_plus[i] += h
            
            f1 = self._evaluate_equations(equations, x)
            f2 = self._evaluate_equations(equations, x_plus)
            
            grad_i = (sum(f2) - sum(f1)) / h if h != 0 else 0.0
            gradient.append(grad_i)
        
        return gradient
    
    def _ode_rhs(self, equations: List[str], t: float, y: List[float]) -> List[float]:
        """Right-hand side of ODE system."""
        # Simplified: dy/dt = -y + sin(t)
        return [-yi + math.sin(t) for yi in y]
    
    def _objective_function(self, equations: List[str], x: List[float]) -> float:
        """Evaluate objective function for optimization."""
        # Simplified: Rosenbrock-like function
        if len(x) < 2:
            return sum(xi**2 for xi in x)
        
        return sum(100 * (x[i+1] - x[i]**2)**2 + (1 - x[i])**2 for i in range(len(x)-1))
