"""Capability Router — Filter models that satisfy a required capability set."""
from llm_gateway.routing.model_router import ModelRouter, ModelInfo


class CapabilityRouter:
    """Select a model whose capability list is a superset of the requested ones.

    Ties are broken by highest ``quality_score`` then lowest ``latency_ms``.
    Returns ``gpt-3.5-turbo`` as a safe default when no candidate matches.
    """

    def __init__(self, models: dict[str, ModelInfo] | None = None):
        self.models = models if models is not None else ModelRouter.MODELS

    def select_model(self, requirements: dict | None = None) -> str:
        requirements = requirements or {}
        needed = set(requirements.get("capabilities", []))

        candidates: list[tuple[str, ModelInfo]] = []
        for name, info in self.models.items():
            caps = set(info.capabilities or [])
            if needed.issubset(caps):
                candidates.append((name, info))

        if not candidates:
            return "gpt-3.5-turbo"

        candidates.sort(key=lambda x: (-x[1].quality_score, x[1].latency_ms))
        return candidates[0][0]

    def matching_models(self, requirements: dict | None = None) -> list[str]:
        """Return every model name that meets the capability requirement."""
        requirements = requirements or {}
        needed = set(requirements.get("capabilities", []))
        return [
            name for name, info in self.models.items()
            if needed.issubset(set(info.capabilities or []))
        ]
