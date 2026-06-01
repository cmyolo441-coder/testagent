"""Latency Router — Pick the fastest model that still meets quality requirements."""
from llm_gateway.routing.model_router import ModelRouter, ModelInfo


class LatencyRouter:
    """Lowest-latency model selector with a quality and capability floor."""

    DEFAULT_MIN_QUALITY = 60.0

    def __init__(self, models: dict[str, ModelInfo] | None = None):
        self.models = models if models is not None else ModelRouter.MODELS

    def select_model(self, requirements: dict | None = None) -> str:
        requirements = requirements or {}
        min_quality = float(requirements.get("min_quality", self.DEFAULT_MIN_QUALITY))
        max_cost = float(requirements.get("max_cost", float("inf")))
        needed = set(requirements.get("capabilities", []))

        candidates: list[tuple[str, ModelInfo]] = []
        for name, info in self.models.items():
            if info.quality_score < min_quality:
                continue
            if info.cost_per_1k_input > max_cost:
                continue
            if needed and not needed.issubset(set(info.capabilities or [])):
                continue
            candidates.append((name, info))

        if not candidates:
            return "gpt-3.5-turbo"

        candidates.sort(key=lambda x: (x[1].latency_ms, -x[1].quality_score))
        return candidates[0][0]

    def latency_of(self, model: str) -> float:
        info = self.models.get(model)
        return info.latency_ms if info else float("inf")
