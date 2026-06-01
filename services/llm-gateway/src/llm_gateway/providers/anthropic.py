"""Anthropic Provider — Claude models integration"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class AnthropicConfig:
    api_key: str = ""
    base_url: str = "https://api.anthropic.com"
    default_model: str = "claude-sonnet-4-20250514"
    timeout: int = 60


class AnthropicProvider:
    """Anthropic API provider."""

    def __init__(self, config: AnthropicConfig = None):
        self.config = config or AnthropicConfig()
        self.client = None

    def _ensure_client(self):
        if self.client is None:
            try:
                import anthropic
                self.client = anthropic.AsyncAnthropic(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout,
                )
            except ImportError:
                raise ImportError("anthropic package not installed: pip install anthropic")

    async def complete(self, request) -> 'LLMResponse':
        self._ensure_client()

        kwargs = {
            "model": request.model or self.config.default_model,
            "max_tokens": request.max_tokens,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        if request.system_prompt:
            kwargs["system"] = request.system_prompt
        if request.stop_sequences:
            kwargs["stop_sequences"] = request.stop_sequences

        response = await self.client.messages.create(**kwargs)

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        return LLMResponse(
            content=content,
            model=response.model,
            provider="anthropic",
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            finish_reason=response.stop_reason or "stop",
        )


from llm_gateway.gateway import LLMResponse
