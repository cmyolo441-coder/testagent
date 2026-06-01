"""Theorem Checker — dispatches a proof obligation to one of several backend
verifiers (Lean, Coq, Isabelle bridges in math-engine). Returns a verdict.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProofObligation:
    id: str
    statement: str
    backend: str = "lean"     # lean | coq | isabelle | symbolic
    proof_script: str = ""


@dataclass
class ProofVerdict:
    accepted: bool
    backend: str
    error: Optional[str] = None
    time_ms: float = 0.0


class TheoremChecker:
    def __init__(self, bridges: Optional[dict] = None):
        # bridges: {"lean": LeanBridge(), ...} — injected from math_engine
        self.bridges = bridges or {}

    def check(self, obligation: ProofObligation) -> ProofVerdict:
        backend = self.bridges.get(obligation.backend)
        if backend is None:
            return ProofVerdict(accepted=False, backend=obligation.backend,
                                error=f"No bridge for backend {obligation.backend}")
        try:
            return backend.verify(obligation.statement, obligation.proof_script)
        except Exception as e:
            return ProofVerdict(accepted=False, backend=obligation.backend, error=str(e))
