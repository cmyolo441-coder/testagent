"""Adversarial Checker — generate refutation attempts against a claim."""
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class AdversarialAttempt:
    strategy: str
    refutation: str
    severity: float


class AdversarialChecker:
    """Drives multiple adversarial strategies. Strategies are pure functions
    taking the claim text and returning (refutation, severity).
    """

    DEFAULT_STRATEGIES = [
        "negation_attack", "edge_case_attack", "scope_attack",
        "definition_attack", "counterexample_attack",
    ]

    def __init__(self):
        self._strategies: dict[str, Callable[[str], tuple[str, float]]] = {}
        # Register built-ins
        self.register("negation_attack", self._negation)
        self.register("edge_case_attack", self._edge_case)
        self.register("scope_attack",     self._scope)
        self.register("definition_attack", self._definition)
        self.register("counterexample_attack", self._counterexample)

    def register(self, name: str, fn: Callable[[str], tuple[str, float]]):
        self._strategies[name] = fn

    def attack(self, claim: str, strategies: Optional[list[str]] = None) -> list[AdversarialAttempt]:
        names = strategies or self.DEFAULT_STRATEGIES
        out = []
        for n in names:
            fn = self._strategies.get(n)
            if not fn: continue
            r, s = fn(claim)
            out.append(AdversarialAttempt(strategy=n, refutation=r, severity=s))
        return out

    # Strategies
    @staticmethod
    def _negation(claim: str) -> tuple[str, float]:
        return f"What if the opposite were true: NOT ({claim})? Find an instance.", 0.6

    @staticmethod
    def _edge_case(claim: str) -> tuple[str, float]:
        return f"At what boundary/limit does '{claim}' break (size→0, scale→∞, time→0)?", 0.7

    @staticmethod
    def _scope(claim: str) -> tuple[str, float]:
        return f"Is '{claim}' really universal, or only valid within a stated scope?", 0.5

    @staticmethod
    def _definition(claim: str) -> tuple[str, float]:
        return f"Which key term in '{claim}' is ambiguous? Re-state under stricter definitions.", 0.5

    @staticmethod
    def _counterexample(claim: str) -> tuple[str, float]:
        return f"Search for one concrete counterexample to '{claim}'.", 0.8
