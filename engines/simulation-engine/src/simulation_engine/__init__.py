"""Simulation Engine — Run what-if scenarios and simulations"""
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
import uuid


@dataclass
class SimulationConfig:
    id: str = field(default_factory=lambda: f"SIM-{uuid.uuid4().hex[:8]}")
    name: str = ""
    parameters: dict = field(default_factory=dict)
    steps: int = 100
    seed: Optional[int] = None


@dataclass
class SimulationResult:
    config_id: str = ""
    steps_completed: int = 0
    outputs: list[dict] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


class SimulationEngine:
    """Run parameterized simulations."""

    def __init__(self):
        self.simulations: dict[str, SimulationConfig] = {}
        self.results: dict[str, SimulationResult] = {}

    def create_simulation(self, name: str, parameters: dict, steps: int = 100) -> SimulationConfig:
        config = SimulationConfig(name=name, parameters=parameters, steps=steps)
        self.simulations[config.id] = config
        return config

    def run(self, config_id: str, step_fn: Callable = None) -> SimulationResult:
        config = self.simulations.get(config_id)
        if not config:
            return SimulationResult(success=False, error="Config not found")

        result = SimulationResult(config_id=config_id)
        state = dict(config.parameters)

        for step in range(config.steps):
            if step_fn:
                try:
                    state = step_fn(state, step)
                    result.outputs.append({"step": step, "state": dict(state)})
                except Exception as e:
                    result.success = False
                    result.error = f"Step {step}: {e}"
                    break
            result.steps_completed = step + 1

        self.results[config_id] = result
        return result
