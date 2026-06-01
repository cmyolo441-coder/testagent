"""Ollama Provider — Local model integration"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class OllamaConfig:
    base_url: str = "http://localhost:11434"
    default_model: str = "llama3"
    timeout: int = 120


class OllamaProvider:
    """Ollama local model provider."""

    def __init__(self, config: OllamaConfig = None):
        self.config = config or OllamaConfig()

    async def complete(self, request) -> 'LLMResponse':
        import httpx

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": request.model or self.config.default_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                f"{self.config.base_url}/api/chat",
                json=payload,
            )
            data = response.json()

        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=data.get("model", self.config.default_model),
            provider="ollama",
            tokens_used=data.get("eval_count", 0) + data.get("prompt_eval_count", 0),
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            latency_ms=data.get("total_duration", 0) / 1_000_000,
        )


from llm_gateway.gateway import LLMResponse
