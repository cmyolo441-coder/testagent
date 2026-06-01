"""NVIDIA NIM (Integrate API) Provider — OpenAI-compatible chat completions.

Endpoint: https://integrate.api.nvidia.com/v1/chat/completions
Auth:     Bearer <NVIDIA_API_KEY>
Models:   stepfun-ai/step-3.7-flash, meta/llama-3.3-70b-instruct, etc.

This provider speaks the OpenAI-compatible REST shape directly via httpx
(no openai SDK dependency), so it works wherever httpx is installed.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NvidiaConfig:
    api_key: str = ""
    base_url: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    default_model: str = "stepfun-ai/step-3.7-flash"
    timeout: int = 60
    extra_headers: dict = field(default_factory=dict)


class NvidiaProvider:
    """NVIDIA Integrate / NIM provider (OpenAI-compatible chat completions)."""

    def __init__(self, config: NvidiaConfig | None = None):
        self.config = config or NvidiaConfig()
        if not self.config.api_key:
            self.config.api_key = os.environ.get("NVIDIA_API_KEY", "")
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            try:
                import httpx  # noqa: F401
            except ImportError as e:
                raise ImportError("httpx not installed: pip install httpx") from e
            import httpx
            self._client = httpx.AsyncClient(timeout=self.config.timeout)

    def _headers(self) -> dict:
        h = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        h.update(self.config.extra_headers or {})
        return h

    def _build_messages(self, request) -> list[dict]:
        msgs: list[dict] = []
        if getattr(request, "system_prompt", "") :
            msgs.append({"role": "system", "content": request.system_prompt})
        msgs.append({"role": "user", "content": request.prompt})
        return msgs

    async def complete(self, request):
        """Async non-streaming completion. Returns LLMResponse."""
        from llm_gateway.gateway import LLMResponse

        self._ensure_client()

        model = request.model or self.config.default_model
        body = {
            "model": model,
            "messages": self._build_messages(request),
            "max_tokens": getattr(request, "max_tokens", 1024),
            "temperature": getattr(request, "temperature", 0.7),
            "stream": False,
        }
        stops = getattr(request, "stop_sequences", None) or []
        if stops:
            body["stop"] = stops

        try:
            resp = await self._client.post(self.config.base_url, headers=self._headers(), json=body)
        except Exception as e:
            return LLMResponse(content="", model=model, provider="nvidia",
                               finish_reason="error", metadata={"error": str(e)})

        if resp.status_code >= 400:
            return LLMResponse(content="", model=model, provider="nvidia",
                               finish_reason="error",
                               metadata={"error": f"HTTP {resp.status_code}: {resp.text[:500]}"})

        try:
            data = resp.json()
        except json.JSONDecodeError:
            return LLMResponse(content=resp.text, model=model, provider="nvidia",
                               finish_reason="error",
                               metadata={"error": "Non-JSON response"})

        choice0 = (data.get("choices") or [{}])[0]
        message = choice0.get("message") or {}
        # Reasoning models (e.g. stepfun-ai/step-3.7-flash) keep the final
        # answer in `content`, but if content is null they expose the
        # chain-of-thought in `reasoning_content`/`reasoning`. Use whichever
        # is non-empty so the gateway never returns "" when text exists.
        content = message.get("content")
        if not content:
            content = message.get("reasoning_content") or message.get("reasoning") or ""
        finish_reason = choice0.get("finish_reason", "stop")

        usage = data.get("usage") or {}
        prompt_tok = int(usage.get("prompt_tokens") or 0)
        completion_tok = int(usage.get("completion_tokens") or 0)
        total_tok = int(usage.get("total_tokens") or (prompt_tok + completion_tok))

        return LLMResponse(
            content=content,
            model=data.get("model", model),
            provider="nvidia",
            tokens_used=total_tok,
            prompt_tokens=prompt_tok,
            completion_tokens=completion_tok,
            finish_reason=finish_reason or "stop",
            metadata={"raw_status": resp.status_code},
        )

    # ------------------------------------------------------------------
    # Sync helper — usable from non-async code (e.g. CLI smoke test).
    # ------------------------------------------------------------------
    def complete_sync(self, prompt: str, model: str | None = None,
                      system_prompt: str = "", max_tokens: int = 512,
                      temperature: float = 0.7) -> dict:
        """Blocking call using httpx.Client. Returns plain dict for easy CLI use."""
        try:
            import httpx
        except ImportError as e:
            raise ImportError("httpx not installed: pip install httpx") from e

        m = model or self.config.default_model
        body = {
            "model": m,
            "messages": ([{"role": "system", "content": system_prompt}] if system_prompt else [])
                        + [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }
        with httpx.Client(timeout=self.config.timeout) as client:
            r = client.post(self.config.base_url, headers=self._headers(), json=body)
        ok = r.status_code < 400
        data = {}
        try:
            data = r.json()
        except Exception:
            pass
        text = ""
        if ok and data:
            try:
                msg = data["choices"][0]["message"]
                text = msg.get("content") or msg.get("reasoning_content") or msg.get("reasoning") or ""
                if not text:
                    text = json.dumps(data)[:500]
            except Exception:
                text = json.dumps(data)[:500]
        return {
            "ok": ok,
            "status": r.status_code,
            "model": m,
            "content": text,
            "raw": data if ok else {"error_body": r.text[:1000]},
            "usage": (data or {}).get("usage", {}),
        }


from llm_gateway.gateway import LLMRequest, LLMResponse  # re-export
