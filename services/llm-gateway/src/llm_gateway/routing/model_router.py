"""Model Router — Select best model for given request"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelInfo:
    name: str
    provider: str
    cost_per_1k_input: float
    cost_per_1k_output: float
    max_tokens: int
    quality_score: float  # 0-100
    latency_ms: float  # average
    capabilities: list[str] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


class ModelRouter:
    """Route requests to optimal model based on strategy."""

    MODELS = {
        "gpt-4": ModelInfo("gpt-4", "openai", 0.03, 0.06, 8192, 95, 2000, ["reasoning", "code", "analysis"]),
        "gpt-4-turbo": ModelInfo("gpt-4-turbo", "openai", 0.01, 0.03, 128000, 93, 1500, ["reasoning", "code", "analysis", "vision"]),
        "gpt-3.5-turbo": ModelInfo("gpt-3.5-turbo", "openai", 0.0005, 0.0015, 16385, 75, 500, ["code", "chat"]),
        "claude-sonnet-4-20250514": ModelInfo("claude-sonnet-4-20250514", "anthropic", 0.003, 0.015, 200000, 92, 1800, ["reasoning", "code", "analysis", "long_context"]),
        "claude-3-5-haiku-20241022": ModelInfo("claude-3-5-haiku-20241022", "anthropic", 0.001, 0.005, 200000, 80, 400, ["code", "chat"]),
        "llama3": ModelInfo("llama3", "ollama", 0, 0, 8192, 70, 300, ["code", "chat"]),
        "stepfun-ai/step-3.7-flash": ModelInfo(
            "stepfun-ai/step-3.7-flash", "nvidia",
            0.0,  # free tier via NVIDIA Integrate; updated if pricing changes
            0.0,
            32768, 82, 600,
            ["code", "chat", "reasoning"],
        ),
    }

    def __init__(self, strategy: str = "quality"):
        self.strategy = strategy

    def select_model(self, requirements: dict = None) -> str:
        requirements = requirements or {}
        needed_capabilities = requirements.get("capabilities", [])
        max_cost = requirements.get("max_cost", float("inf"))
        max_latency = requirements.get("max_latency", float("inf"))
        min_quality = requirements.get("min_quality", 0)

        candidates = []
        for name, info in self.MODELS.items():
            if info.cost_per_1k_input > max_cost:
                continue
            if info.latency_ms > max_latency:
                continue
            if info.quality_score < min_quality:
                continue
            if needed_capabilities:
                if not all(c in info.capabilities for c in needed_capabilities):
                    continue
            candidates.append((name, info))

        if not candidates:
            return "gpt-3.5-turbo"

        if self.strategy == "quality":
            candidates.sort(key=lambda x: x[1].quality_score, reverse=True)
        elif self.strategy == "cost":
            candidates.sort(key=lambda x: x[1].cost_per_1k_input)
        elif self.strategy == "latency":
            candidates.sort(key=lambda x: x[1].latency_ms)
        elif self.strategy == "balanced":
            candidates.sort(key=lambda x: (
                x[1].quality_score * 0.4 +
                (1 - x[1].cost_per_1k_input / 0.05) * 30 +
                (1 - x[1].latency_ms / 2000) * 30
            ), reverse=True)

        return candidates[0][0]

    def get_model_info(self, model: str) -> Optional[ModelInfo]:
        return self.MODELS.get(model)

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        info = self.MODELS.get(model)
        if not info:
            return 0
        return (input_tokens / 1000 * info.cost_per_1k_input +
                output_tokens / 1000 * info.cost_per_1k_output)
