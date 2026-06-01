"""DeepSeek Provider — OpenAI-compatible DeepSeek API"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class DeepSeekConfig:
    api_key: str = ""
    base_url: str = "https://api.deepseek.com/v1"
    default_model: str = "deepseek-chat"
    timeout: int = 60


class DeepSeekProvider:
    """DeepSeek API provider (OpenAI-compatible)."""

    def __init__(self, config: DeepSeekConfig = None):
        self.config = config or DeepSeekConfig()
        self.client = None

    def _ensure_client(self):
        if self.client is None:
            try:
                import openai
                self.client = openai.AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout,
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
            provider="deepseek",
            tokens_used=tokens_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason=choice.finish_reason or "stop",
        )


from llm_gateway.gateway import LLMRequest, LLMResponse
