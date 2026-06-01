"""OpenRouter Provider — multi-model gateway via OpenRouter"""
from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class OpenRouterConfig:
    api_key: str = ""
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "openrouter/auto"
    timeout: int = 60
    http_referer: Optional[str] = None
    x_title: Optional[str] = None


class OpenRouterProvider:
    """OpenRouter API provider (OpenAI-compatible, arbitrary model passthrough)."""

    def __init__(self, config: OpenRouterConfig = None):
        self.config = config or OpenRouterConfig()
        self.client = None

    def _ensure_client(self):
        if self.client is None:
            try:
                import openai
                default_headers: Dict[str, str] = {}
                if self.config.http_referer:
                    default_headers["HTTP-Referer"] = self.config.http_referer
                if self.config.x_title:
                    default_headers["X-Title"] = self.config.x_title
                self.client = openai.AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout,
                    default_headers=default_headers or None,
                )
            except ImportError:
                raise ImportError("openai package not installed: pip install openai")

    async def complete(self, request: 'LLMRequest') -> 'LLMResponse':
        self._ensure_client()

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        response = await self.client.chat.completions.create(
            model=request.model or self.config.default_model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop_sequences or None,
        )

        choice = response.choices[0]
        content = choice.message.content or ""
        usage = getattr(response, "usage", None)
        if usage:
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            tokens_used = usage.total_tokens
        else:
            prompt_tokens = len(request.prompt.split())
            completion_tokens = len(content.split())
            tokens_used = prompt_tokens + completion_tokens

        return LLMResponse(
            content=content,
            model=response.model,
            provider="openrouter",
            tokens_used=tokens_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason=choice.finish_reason or "stop",
        )


from llm_gateway.gateway import LLMRequest, LLMResponse
