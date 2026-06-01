"""Self-Consistency Checker — Detect contradictions in recent statements/actions."""
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Common negation cues for naive subject/polarity extraction.
_NEG_TOKENS = {
    "not", "no", "never", "none", "cannot", "can't", "won't", "wouldn't",
    "shouldn't", "doesn't", "don't", "didn't", "isn't", "aren't",
}

_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "i", "you", "we", "they", "he", "she", "it", "of", "in", "to", "on",
    "and", "or", "but", "for", "with", "as", "at", "by", "this", "that",
    "these", "those", "will", "would", "should", "can", "could", "may",
    "might", "must", "do", "does", "did", "have", "has", "had", "very",
    "really", "just", "so", "than", "then",
}


@dataclass
class Statement:
    id: str = field(default_factory=lambda: f"STMT-{uuid.uuid4().hex[:8]}")
    text: str = ""
    timestamp: str = field(default_factory=_now_iso)
    source: str = "agent"  # agent, user, tool, system
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "timestamp": self.timestamp,
            "source": self.source,
            "metadata": dict(self.metadata),
        }


@dataclass
class Contradiction:
    stmt_a: Statement
    stmt_b: Statement
    subject: str
    confidence: float  # 0.0 - 1.0
    rationale: str = ""

    def to_dict(self) -> dict:
        return {
            "stmt_a": self.stmt_a.to_dict(),
            "stmt_b": self.stmt_b.to_dict(),
            "subject": self.subject,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[A-Za-z']+", (text or "").lower())]


def _polarity_and_subject(text: str) -> tuple[bool, set[str]]:
    """Return (is_negated, content_tokens). Negation = odd count of negation cues."""
    toks = _tokenize(text)
    neg_count = sum(1 for t in toks if t in _NEG_TOKENS)
    content = {t for t in toks if t not in _NEG_TOKENS and t not in _STOPWORDS}
    return (neg_count % 2 == 1), content


class SelfConsistencyChecker:
    """Scan statements for opposite assertions on the same subject."""

    def __init__(self, overlap_threshold: int = 2):
        self.overlap_threshold = overlap_threshold
        self.statements: list[Statement] = []

    def add_statement(self, text: str, source: str = "agent",
                      timestamp: Optional[str] = None,
                      metadata: Optional[dict] = None) -> Statement:
        s = Statement(
            text=text,
            source=source,
            timestamp=timestamp or _now_iso(),
            metadata=dict(metadata or {}),
        )
        self.statements.append(s)
        return s

    def scan(self, statements: Optional[list[Statement]] = None) -> list[Contradiction]:
        pool = statements if statements is not None else self.statements
        analyzed = [(s, *_polarity_and_subject(s.text)) for s in pool]

        contradictions: list[Contradiction] = []
        for i in range(len(analyzed)):
            s_a, neg_a, toks_a = analyzed[i]
            for j in range(i + 1, len(analyzed)):
                s_b, neg_b, toks_b = analyzed[j]
                if neg_a == neg_b:
                    continue
                overlap = toks_a & toks_b
                if len(overlap) < self.overlap_threshold:
                    continue
                # Confidence proportional to overlap ratio.
                ratio = len(overlap) / max(1, min(len(toks_a), len(toks_b)))
                confidence = round(min(1.0, 0.4 + 0.6 * ratio), 3)
                subject = " ".join(sorted(overlap))
                contradictions.append(Contradiction(
                    stmt_a=s_a,
                    stmt_b=s_b,
                    subject=subject,
                    confidence=confidence,
                    rationale=(
                        f"Opposite polarity on shared tokens "
                        f"({len(overlap)}/{min(len(toks_a), len(toks_b))} overlap)"
                    ),
                ))
        # Sort highest confidence first.
        contradictions.sort(key=lambda c: c.confidence, reverse=True)
        return contradictions

    def clear(self) -> None:
        self.statements.clear()
