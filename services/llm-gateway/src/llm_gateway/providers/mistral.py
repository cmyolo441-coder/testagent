"""Mistral Provider — Mistral AI integration"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class MistralConfig:
    api_key: str = ""
    base_url: str = "https://api.mistral.ai"
    default_model: str = "mistral-large-latest"
    timeout: int = 60


class MistralProvider:
    """Mistral AI API provider."""

    def __init__(self, config: MistralConfig = None):
        self.config = config or MistralConfig()
        self.client = None

    def _ensure_client(self):
        if self.client is None:
            try:
                from mistralai import Mistral
                self.client = Mistral(
                    api_key=self.config.api_key,
                    server_url=self.config.base_url,
                )
            except ImportError:
                raise ImportError("mistralai package not installed: pip install mistralai")

    async def complete(self, request: 'LLMRequest') -> 'LLMResponse':
        self._ensure_client()

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        kwargs = {
            "model": request.model or self.config.default_model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        if request.stop_sequences:
            kwargs["stop"] = request.stop_sequences

        response = await self.client.chat.complete_async(**kwargs)

        choice = response.choices[0]
        content = choice.message.content or ""
        usage = getattr(response, "usage", None)
        if usage:
            prompt_tokens = getattr(usage, "prompt_tokens", 0)
            completion_tokens = getattr(usage, "completion_tokens", 0)
            tokens_used = getattr(usage, "total_tokens", prompt_tokens + completion_tokens)
        else:
            prompt_tokens = len(request.prompt.split())
            completion_tokens = len(content.split())
            tokens_used = prompt_tokens + completion_tokens

        return LLMResponse(
            content=content,
            model=response.model,
            provider="mistral",
            tokens_used=tokens_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason=getattr(choice, "finish_reason", None) or "stop",
        )


from llm_gateway.gateway import LLMRequest, LLMResponse
