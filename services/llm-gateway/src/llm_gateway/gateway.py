"""LLM Gateway — Route requests to appropriate providers"""
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime, timezone
import json


@dataclass
class LLMRequest:
    prompt: str = ""
    model: str = "default"
    max_tokens: int = 4096
    temperature: float = 0.7
    system_prompt: str = ""
    stop_sequences: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class LLMResponse:
    content: str = ""
    model: str = ""
    provider: str = ""
    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    finish_reason: str = "stop"
    latency_ms: float = 0
    cost: float = 0
    cached: bool = False
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "content": self.content[:200],
            "model": self.model,
            "provider": self.provider,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "cost": self.cost,
            "finish_reason": self.finish_reason,
        }


class LLMGateway:
    """Central gateway for LLM interactions with routing and fallback."""

    def __init__(self):
        self.providers: dict[str, Any] = {}
        self.routing_strategy: str = "quality"  # quality, cost, latency, fallback
        self.default_model: str = "gpt-4"
        self.fallback_chain: list[str] = []
        self.request_history: list[dict] = []
        self.total_tokens: int = 0
        self.total_cost: float = 0

    def register_provider(self, name: str, provider: Any):
        self.providers[name] = provider

    def set_fallback_chain(self, chain: list[str]):
        self.fallback_chain = chain

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Send completion request with automatic routing and fallback."""
        provider_name = self._select_provider(request)
        provider = self.providers.get(provider_name)

        if not provider:
            return LLMResponse(
                content="",
                error=f"No provider available for model: {request.model}",
                finish_reason="error",
            )

        try:
            start = datetime.now(timezone.utc)
            response = await provider.complete(request)
            latency = (datetime.now(timezone.utc) - start).total_seconds() * 1000

            response.latency_ms = latency
            response.provider = provider_name

            self.total_tokens += response.tokens_used
            self.total_cost += response.cost
            self.request_history.append({
                "model": request.model,
                "provider": provider_name,
                "tokens": response.tokens_used,
                "latency_ms": latency,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            return response
        except Exception as e:
            # Try fallback
            for fallback_name in self.fallback_chain:
                if fallback_name != provider_name:
                    fallback_provider = self.providers.get(fallback_name)
                    if fallback_provider:
                        try:
                            return await fallback_provider.complete(request)
                        except Exception:
                            continue
            return LLMResponse(
                content="",
                error=str(e),
                finish_reason="error",
            )

    def _select_provider(self, request: LLMRequest) -> str:
        if request.model in self.providers:
            return request.model
        return self.default_model

    def get_stats(self) -> dict:
        return {
            "total_requests": len(self.request_history),
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "providers": list(self.providers.keys()),
            "avg_latency": sum(r.get("latency_ms", 0) for r in self.request_history) / max(len(self.request_history), 1),
        }
