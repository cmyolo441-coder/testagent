"""Gemini Provider — Google Generative AI integration"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class GeminiConfig:
    api_key: str = ""
    default_model: str = "gemini-1.5-pro"
    timeout: int = 60


class GeminiProvider:
    """Google Gemini API provider."""

    def __init__(self, config: GeminiConfig = None):
        self.config = config or GeminiConfig()
        self.client = None
        self._genai = None

    def _ensure_client(self):
        if self.client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.config.api_key)
                self._genai = genai
                self.client = True
            except ImportError:
                raise ImportError("google-generativeai package not installed: pip install google-generativeai")

    async def complete(self, request: 'LLMRequest') -> 'LLMResponse':
        self._ensure_client()

        model_name = request.model or self.config.default_model
        system_instruction = request.system_prompt or None

        model = self._genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction,
        )

        generation_config = {
            "max_output_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        if request.stop_sequences:
            generation_config["stop_sequences"] = request.stop_sequences

        response = await model.generate_content_async(
            request.prompt,
            generation_config=generation_config,
        )

        content = response.text or ""
        usage = getattr(response, "usage_metadata", None)
        if usage:
            prompt_tokens = getattr(usage, "prompt_token_count", 0)
            completion_tokens = getattr(usage, "candidates_token_count", 0)
            tokens_used = prompt_tokens + completion_tokens
        else:
            prompt_tokens = len(request.prompt.split())
            completion_tokens = len(content.split())
            tokens_used = prompt_tokens + completion_tokens

        finish_reason = "stop"
        if response.candidates:
            fr = getattr(response.candidates[0], "finish_reason", None)
            if fr is not None:
                finish_reason = str(fr).lower()

        return LLMResponse(
            content=content,
            model=model_name,
            provider="gemini",
            tokens_used=tokens_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason=finish_reason,
        )


from llm_gateway.gateway import LLMRequest, LLMResponse
