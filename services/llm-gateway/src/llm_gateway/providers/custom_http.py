"""Custom HTTP Provider — generic adapter for arbitrary LLM HTTP endpoints"""
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class CustomHTTPConfig:
    base_url: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    request_template: str = '{"model": "{model}", "prompt": "{prompt}"}'
    response_path: str = "choices.0.text"
    default_model: str = "custom"
    method: str = "POST"
    timeout: int = 60


class CustomHTTPProvider:
    """Generic HTTP adapter: templated request body + dot-path response extraction."""

    def __init__(self, config: CustomHTTPConfig = None):
        self.config = config or CustomHTTPConfig()
        self.client = None
        self._httpx = None

    def _ensure_client(self):
        if self.client is None:
            try:
                import httpx
                self._httpx = httpx
                self.client = httpx.AsyncClient(timeout=self.config.timeout)
            except ImportError:
                raise ImportError("httpx package not installed: pip install httpx")

    def _render_template(self, request: 'LLMRequest') -> str:
        model = request.model or self.config.default_model
        prompt_escaped = json.dumps(request.prompt)[1:-1]
        system_escaped = json.dumps(request.system_prompt or "")[1:-1]
        rendered = self.config.request_template
        rendered = rendered.replace("{prompt}", prompt_escaped)
        rendered = rendered.replace("{model}", model)
        rendered = rendered.replace("{system}", system_escaped)
        rendered = rendered.replace("{max_tokens}", str(request.max_tokens))
        rendered = rendered.replace("{temperature}", str(request.temperature))
        return rendered

    def _extract(self, data: Any, path: str) -> str:
        cur = data
        for part in path.split("."):
            if part == "":
                continue
            if isinstance(cur, list):
                try:
                    cur = cur[int(part)]
                except (ValueError, IndexError):
                    return ""
            elif isinstance(cur, dict):
                cur = cur.get(part, "")
            else:
                return ""
        return cur if isinstance(cur, str) else json.dumps(cur)

    async def complete(self, request: 'LLMRequest') -> 'LLMResponse':
        self._ensure_client()

        body_str = self._render_template(request)
        try:
            body = json.loads(body_str)
        except json.JSONDecodeError:
            body = body_str

        headers = dict(self.config.headers or {})
        headers.setdefault("Content-Type", "application/json")

        response = await self.client.request(
            self.config.method,
            self.config.base_url,
            headers=headers,
            json=body if isinstance(body, (dict, list)) else None,
            content=body if isinstance(body, str) else None,
        )
        response.raise_for_status()
        data = response.json()

        content = self._extract(data, self.config.response_path) or ""
        model = request.model or self.config.default_model
        prompt_tokens = len(request.prompt.split())
        completion_tokens = len(content.split())
        tokens_used = prompt_tokens + completion_tokens

        return LLMResponse(
            content=content,
            model=model,
            provider="custom_http",
            tokens_used=tokens_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason="stop",
        )


from llm_gateway.gateway import LLMRequest, LLMResponse
