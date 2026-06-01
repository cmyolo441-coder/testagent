"""Independent Verifier — fan out verification of a claim across N independent
checkers (different prompts/methods) and aggregate by majority + confidence.
"""
from dataclasses import dataclass, field
from typing import Callable
import statistics


@dataclass
class VerifierVote:
    verifier: str
    verdict: str           # "supported" | "refuted" | "inconclusive"
    confidence: float
    rationale: str = ""


@dataclass
class IndependentVerificationResult:
    claim: str
    votes: list[VerifierVote]
    majority_verdict: str
    aggregate_confidence: float
    unanimity: bool

    def to_dict(self) -> dict:
        return {
            "claim": self.claim,
            "majority_verdict": self.majority_verdict,
            "aggregate_confidence": round(self.aggregate_confidence, 3),
            "unanimity": self.unanimity,
            "votes": [v.__dict__ for v in self.votes],
        }


class IndependentVerifier:
    def __init__(self):
        self._checkers: list[Callable[[str], VerifierVote]] = []

    def register(self, name: str, fn: Callable[[str], dict]) -> None:
        def wrapped(claim: str) -> VerifierVote:
            r = fn(claim) or {}
            return VerifierVote(
                verifier=name,
                verdict=r.get("verdict", "inconclusive"),
                confidence=float(r.get("confidence", 0.5)),
                rationale=r.get("rationale", ""),
            )
        self._checkers.append(wrapped)

    def verify(self, claim: str) -> IndependentVerificationResult:
        votes = [c(claim) for c in self._checkers] if self._checkers else [
            VerifierVote("default", "inconclusive", 0.5, "no checkers registered")
        ]
        counts = {"supported": 0, "refuted": 0, "inconclusive": 0}
        for v in votes:
            counts[v.verdict] = counts.get(v.verdict, 0) + 1
        majority = max(counts, key=counts.get)
        confs = [v.confidence for v in votes if v.verdict == majority]
        agg = statistics.mean(confs) if confs else 0.5
        return IndependentVerificationResult(
            claim=claim, votes=votes,
            majority_verdict=majority,
            aggregate_confidence=agg,
            unanimity=len({v.verdict for v in votes}) == 1,
        )
