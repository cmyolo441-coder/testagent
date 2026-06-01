"""Fallback Router — Ordered chain with health checks and cooldowns."""
import time
from typing import Callable, Optional

from llm_gateway.routing.model_router import ModelRouter, ModelInfo


class FallbackRouter:
    """Try an ordered list of models, skipping any that are unhealthy or cooling down.

    ``health_check`` is invoked with the provider name and must return ``True``
    when the provider is reachable. ``record_failure`` puts a model into a
    cooldown window so transient errors don't immediately recur.
    """

    DEFAULT_COOLDOWN_SEC = 30.0

    def __init__(
        self,
        chain: list[str],
        health_check: Optional[Callable[[str], bool]] = None,
        cooldown_sec: float = DEFAULT_COOLDOWN_SEC,
        models: dict[str, ModelInfo] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.chain = list(chain)
        self.health_check = health_check or (lambda _provider: True)
        self.cooldown_sec = float(cooldown_sec)
        self.models = models if models is not None else ModelRouter.MODELS
        self._clock = clock
        # model_name -> timestamp at which the cooldown expires
        self._cooldowns: dict[str, float] = {}
        # model_name -> consecutive failure count (informational)
        self._failure_counts: dict[str, int] = {}

    def select_model(self, requirements: dict | None = None) -> str:
        now = self._clock()
        last_known: Optional[str] = None
        for model_name in self.chain:
            info = self.models.get(model_name)
            if info is None:
                continue
            last_known = model_name
            # Skip models in cooldown.
            if self._cooldowns.get(model_name, 0.0) > now:
                continue
            try:
                if not self.health_check(info.provider):
                    continue
            except Exception:
                continue
            return model_name

        # Everything is unhealthy or cooling down. Return the last known model
        # so the caller still has something to attempt.
        return last_known or (self.chain[0] if self.chain else "gpt-3.5-turbo")

    def record_failure(self, model: str) -> None:
        """Record a failure and start a cooldown timer (exponential up to 5 min)."""
        count = self._failure_counts.get(model, 0) + 1
        self._failure_counts[model] = count
        # Backoff: cooldown * 2^(count-1), capped at 300 seconds.
        backoff = min(self.cooldown_sec * (2 ** (count - 1)), 300.0)
        self._cooldowns[model] = self._clock() + backoff

    def record_success(self, model: str) -> None:
        """Clear any cooldown state for ``model``."""
        self._failure_counts.pop(model, None)
        self._cooldowns.pop(model, None)

    def is_available(self, model: str) -> bool:
        return self._cooldowns.get(model, 0.0) <= self._clock()
