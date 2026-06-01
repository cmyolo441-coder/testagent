"""Cost Router — Pick the cheapest model that still meets a quality floor."""
from llm_gateway.routing.model_router import ModelRouter, ModelInfo


class CostRouter:
    """Cheapest-first model selector with a configurable quality floor."""

    DEFAULT_MIN_QUALITY = 60.0

    def __init__(self, models: dict[str, ModelInfo] | None = None):
        self.models = models if models is not None else ModelRouter.MODELS

    def _blended_cost(self, info: ModelInfo) -> float:
        """Approximate per-1k blended cost assuming a 1:1 in/out ratio."""
        return info.cost_per_1k_input + info.cost_per_1k_output

    def select_model(self, requirements: dict | None = None) -> str:
        requirements = requirements or {}
        min_quality = float(requirements.get("min_quality", self.DEFAULT_MIN_QUALITY))
        needed = set(requirements.get("capabilities", []))
        max_latency = float(requirements.get("max_latency", float("inf")))

        candidates: list[tuple[str, ModelInfo]] = []
        for name, info in self.models.items():
            if info.quality_score < min_quality:
                continue
            if info.latency_ms > max_latency:
                continue
            if needed and not needed.issubset(set(info.capabilities or [])):
                continue
            candidates.append((name, info))

        if not candidates:
            return "gpt-3.5-turbo"

        candidates.sort(key=lambda x: (self._blended_cost(x[1]), -x[1].quality_score))
        return candidates[0][0]

    def estimate_total(self, model: str, est_in_tokens: int, est_out_tokens: int) -> float:
        """Return projected USD cost for a single request."""
        info = self.models.get(model)
        if info is None:
            return 0.0
        return (
            (est_in_tokens / 1000.0) * info.cost_per_1k_input
            + (est_out_tokens / 1000.0) * info.cost_per_1k_output
        )
