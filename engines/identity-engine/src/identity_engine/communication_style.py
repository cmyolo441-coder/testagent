"""Communication Style — Tunable presentation layer for agent output."""
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Heuristic contractions and informal -> formal swaps
_INFORMAL_TO_FORMAL = {
    r"\bdon't\b": "do not",
    r"\bdoesn't\b": "does not",
    r"\bcan't\b": "cannot",
    r"\bwon't\b": "will not",
    r"\bI'm\b": "I am",
    r"\bit's\b": "it is",
    r"\bthat's\b": "that is",
    r"\bwe're\b": "we are",
    r"\byou're\b": "you are",
    r"\bgonna\b": "going to",
    r"\bwanna\b": "want to",
    r"\bkinda\b": "somewhat",
    r"\byeah\b": "yes",
    r"\bnope\b": "no",
}

_FORMAL_TO_INFORMAL = {
    r"\bdo not\b": "don't",
    r"\bcannot\b": "can't",
    r"\bwill not\b": "won't",
    r"\bI am\b": "I'm",
    r"\bit is\b": "it's",
    r"\bthat is\b": "that's",
}

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F6FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA70-\U0001FAFF"
    "☀-➿"
    "]+",
    flags=re.UNICODE,
)


@dataclass
class CommunicationStyle:
    id: str = field(default_factory=lambda: f"STYLE-{uuid.uuid4().hex[:8]}")
    tone: str = "neutral"  # warm, neutral, terse, playful, authoritative
    formality: float = 0.5  # 0 = casual, 1 = formal
    verbosity: float = 0.5  # 0 = terse, 1 = detailed
    language_preference: str = "en"
    emoji_allowed: bool = False
    technical_depth: str = "medium"  # low, medium, high, expert
    examples_dict: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tone": self.tone,
            "formality": self.formality,
            "verbosity": self.verbosity,
            "language_preference": self.language_preference,
            "emoji_allowed": self.emoji_allowed,
            "technical_depth": self.technical_depth,
            "examples_dict": dict(self.examples_dict),
            "created_at": self.created_at,
        }

    def _apply_formality(self, text: str) -> str:
        if self.formality >= 0.6:
            for pat, repl in _INFORMAL_TO_FORMAL.items():
                text = re.sub(pat, repl, text, flags=re.IGNORECASE)
        elif self.formality <= 0.3:
            for pat, repl in _FORMAL_TO_INFORMAL.items():
                text = re.sub(pat, repl, text, flags=re.IGNORECASE)
        return text

    def _apply_verbosity(self, text: str) -> str:
        if self.verbosity <= 0.25:
            # Terse: collapse multiple whitespace; keep only first 2 sentences.
            sentences = re.split(r"(?<=[.!?])\s+", text.strip())
            kept = [s for s in sentences if s][:2]
            return " ".join(kept)
        if self.verbosity >= 0.75 and text and not text.endswith("\n"):
            # Slight expansion hint.
            return text
        return text

    def _apply_emoji(self, text: str) -> str:
        if not self.emoji_allowed:
            text = _EMOJI_RE.sub("", text)
            # Clean double spaces left by emoji removal.
            text = re.sub(r"[ \t]{2,}", " ", text).strip()
        return text

    def _apply_tone(self, text: str) -> str:
        tone = (self.tone or "").lower()
        if not text:
            return text
        if tone == "terse":
            # Strip filler words.
            return re.sub(r"\b(just|really|very|actually|basically)\s+", "", text, flags=re.IGNORECASE)
        if tone == "warm" and self.formality < 0.7:
            if not re.search(r"\b(thanks|please|happy to)\b", text, flags=re.IGNORECASE):
                text = text.rstrip()
                text = text + (" — happy to help." if not text.endswith(".") else " Happy to help.")
        if tone == "authoritative":
            text = re.sub(r"\bI think\b", "I conclude", text, flags=re.IGNORECASE)
            text = re.sub(r"\bmaybe\b", "likely", text, flags=re.IGNORECASE)
        return text

    def apply(self, text: str) -> str:
        """Apply heuristic transforms producing an adjusted text."""
        if not text:
            return text
        out = text
        out = self._apply_emoji(out)
        out = self._apply_formality(out)
        out = self._apply_tone(out)
        out = self._apply_verbosity(out)
        return out.strip()
