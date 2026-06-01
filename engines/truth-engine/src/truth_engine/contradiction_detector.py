"""Contradiction Detector — pairwise contradiction signal for claims.

Heuristics combined:
 - negation flip on same subject+predicate
 - antonym pair detection (small bundled lexicon)
 - numerical disagreement on same subject
"""
from dataclasses import dataclass
import re


ANTONYMS = {
    "increase": "decrease", "rise": "fall", "up": "down",
    "more": "less", "before": "after", "true": "false",
    "exists": "absent", "always": "never",
}


@dataclass
class Contradiction:
    claim_a: str
    claim_b: str
    kind: str          # "negation" | "antonym" | "numeric" | "temporal"
    confidence: float
    detail: str


class ContradictionDetector:
    NUMBER = re.compile(r"-?\d+(?:\.\d+)?")

    def detect_pairs(self, claims: list[str]) -> list[Contradiction]:
        out: list[Contradiction] = []
        for i, a in enumerate(claims):
            for b in claims[i + 1:]:
                c = self._compare(a, b)
                if c: out.append(c)
        return out

    def _compare(self, a: str, b: str):
        al, bl = a.lower(), b.lower()
        # Negation
        if self._strip_neg(al) == self._strip_neg(bl) and self._has_negation(al) != self._has_negation(bl):
            return Contradiction(a, b, "negation", 0.85, "One claim negates the other")

        # Antonym swap
        for word, anti in ANTONYMS.items():
            if word in al and anti in bl and self._shared_subject(al, bl):
                return Contradiction(a, b, "antonym", 0.7, f"'{word}' vs '{anti}'")

        # Numeric disagreement on shared subject
        na = self.NUMBER.findall(a)
        nb = self.NUMBER.findall(b)
        if na and nb and self._shared_subject(al, bl):
            if set(na) != set(nb):
                return Contradiction(a, b, "numeric", 0.6, f"Numbers {na} vs {nb}")
        return None

    @staticmethod
    def _has_negation(s: str) -> bool:
        return any(n in s.split() for n in ("not", "no", "never", "without"))

    @staticmethod
    def _strip_neg(s: str) -> str:
        for n in ("not ", "no ", "never ", "without "):
            s = s.replace(n, "")
        return s

    @staticmethod
    def _shared_subject(a: str, b: str) -> bool:
        wa = set(re.findall(r"\w+", a))
        wb = set(re.findall(r"\w+", b))
        shared = wa & wb
        # Need more than just stopwords overlapping
        meaningful = shared - {"a", "the", "is", "are", "of", "in", "on", "and", "to"}
        return len(meaningful) >= 2
