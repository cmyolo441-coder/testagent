"""Policy Router — Rule-driven model preference with a balanced fallback."""
from dataclasses import dataclass, field
from typing import Optional

from llm_gateway.routing.model_router import ModelRouter, ModelInfo


@dataclass
class Rule:
    """A single routing rule.

    ``when`` is a dict of conditions that must all match the merged
    ``requirements`` + ``context`` mapping. ``prefer_model`` is the model name
    to return when the rule fires. Higher ``priority`` rules win ties.
    """
    when: dict = field(default_factory=dict)
    prefer_model: str = ""
    priority: int = 0
    name: str = ""

    def matches(self, fields: dict) -> bool:
        for key, expected in self.when.items():
            actual = fields.get(key)
            if isinstance(expected, (list, tuple, set)):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        return True


class PolicyRouter:
    """Evaluate a list of ``Rule`` objects, falling back to the balanced router."""

    def __init__(
        self,
        rules: Optional[list[Rule]] = None,
        models: dict[str, ModelInfo] | None = None,
        fallback_strategy: str = "balanced",
    ):
        self.rules: list[Rule] = list(rules or [])
        self.models = models if models is not None else ModelRouter.MODELS
        self._fallback = ModelRouter(strategy=fallback_strategy)

    def add_rule(self, rule: Rule) -> None:
        self.rules.append(rule)

    def evaluate(self, requirements: dict | None = None, context: dict | None = None) -> str:
        requirements = requirements or {}
        context = context or {}
        merged = {**requirements, **context}

        # Sort rules by descending priority so explicit overrides win.
        ordered = sorted(self.rules, key=lambda r: -r.priority)
        for rule in ordered:
            if rule.matches(merged) and rule.prefer_model in self.models:
                return rule.prefer_model

        return self._fallback.select_model(requirements)

    # Convenience alias used by some callers.
    def select_model(self, requirements: dict | None = None, context: dict | None = None) -> str:
        return self.evaluate(requirements, context)
