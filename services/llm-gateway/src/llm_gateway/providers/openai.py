"""OpenAI Provider — GPT models integration"""
import json
from typing import Optional
from dataclasses import dataclass


@dataclass
class OpenAIConfig:
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    organization: Optional[str] = None
    default_model: str = "gpt-4"
    timeout: int = 60


class OpenAIProvider:
    """OpenAI API provider."""

    def __init__(self, config: OpenAIConfig = None):
        self.config = config or OpenAIConfig()
        self.client = None

    def _ensure_client(self):
        if self.client is None:
            try:
                import openai
                self.client = openai.AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    organization=self.config.organization,
                    timeout=self.config.timeout,
                )
            except ImportError:
                raise ImportError("openai package not installed: pip install openai")

    async def complete(self, request) -> 'LLMResponse':
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
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            provider="openai",
            tokens_used=response.usage.total_tokens,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            finish_reason=choice.finish_reason or "stop",
        )


from llm_gateway.gateway import LLMResponse
