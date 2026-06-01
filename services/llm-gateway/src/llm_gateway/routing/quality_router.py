"""Quality Router — Pick the highest-quality model under cost/latency caps."""
from llm_gateway.routing.model_router import ModelRouter, ModelInfo


class QualityRouter:
    """Maximize quality subject to ``max_cost`` and ``max_latency`` ceilings."""

    def __init__(self, models: dict[str, ModelInfo] | None = None):
        self.models = models if models is not None else ModelRouter.MODELS

    def select_model(self, requirements: dict | None = None) -> str:
        requirements = requirements or {}
        max_cost = float(requirements.get("max_cost", float("inf")))
        max_latency = float(requirements.get("max_latency", float("inf")))
        needed = set(requirements.get("capabilities", []))

        candidates: list[tuple[str, ModelInfo]] = []
        for name, info in self.models.items():
            if info.cost_per_1k_input > max_cost:
                continue
            if info.latency_ms > max_latency:
                continue
            if needed and not needed.issubset(set(info.capabilities or [])):
                continue
            candidates.append((name, info))

        if not candidates:
            # No model fits both caps; return best overall quality as a soft default.
            best = max(self.models.items(), key=lambda x: x[1].quality_score, default=None)
            return best[0] if best else "gpt-3.5-turbo"

        candidates.sort(key=lambda x: (-x[1].quality_score, x[1].cost_per_1k_input, x[1].latency_ms))
        return candidates[0][0]

    def quality_of(self, model: str) -> float:
        info = self.models.get(model)
        return info.quality_score if info else 0.0
