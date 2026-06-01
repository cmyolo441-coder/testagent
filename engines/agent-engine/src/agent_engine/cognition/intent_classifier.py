"""Intent Classifier — Maps natural-language user text to typed Intents."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import re
import uuid


INTENT_RULES: dict[str, dict] = {
    "ask_question": {
        "patterns": [
            r"\?\s*$",
            r"^\s*(what|why|how|when|where|who|which|can you tell|explain|describe)\b",
            r"\bdo you know\b",
        ],
        "keywords": ["explain", "describe", "definition", "meaning"],
        "weight": 1.0,
    },
    "request_action": {
        "patterns": [
            r"^\s*(please\s+)?(run|execute|deploy|build|create|make|generate|fetch|download|install|start|stop|restart|kill)\b",
            r"\bcould you\s+(run|do|execute|build|deploy)\b",
            r"^\s*do\s+",
        ],
        "keywords": ["please", "do it", "execute", "run", "deploy"],
        "weight": 1.0,
    },
    "set_goal": {
        "patterns": [
            r"\b(i want|i'd like|i would like|we want|we need|let's|lets)\s+to\b",
            r"^\s*goal\s*[:=]",
            r"\b(objective|target|mission)\s*[:=]?",
            r"\bin\s+\d+\s+(day|days|week|weeks|month|months|year|years)\b",
        ],
        "keywords": ["goal", "objective", "milestone", "deadline"],
        "weight": 1.0,
    },
    "request_help": {
        "patterns": [
            r"\bhelp\b",
            r"\bassist(ance)?\b",
            r"\bstuck\b",
            r"\bnot sure\b",
            r"\bhow do i\b",
        ],
        "keywords": ["help", "support", "stuck", "confused"],
        "weight": 1.0,
    },
    "give_feedback": {
        "patterns": [
            r"\b(good|great|nice|excellent|bad|wrong|incorrect|poor|terrible)\b",
            r"\bfeedback\b",
            r"\b(i (like|love|hate|dislike))\b",
        ],
        "keywords": ["feedback", "rating", "review"],
        "weight": 0.9,
    },
    "cancel": {
        "patterns": [
            r"^\s*(cancel|abort|stop|halt|nevermind|never mind|quit)\b",
            r"\bcancel\s+(it|that|this|the)\b",
        ],
        "keywords": ["cancel", "abort", "stop", "halt"],
        "weight": 1.2,
    },
    "approve": {
        "patterns": [
            r"^\s*(yes|y|ok|okay|approve|approved|go ahead|proceed|confirm|sure|sounds good|do it|lgtm)\b",
            r"\bi approve\b",
        ],
        "keywords": ["approve", "yes", "confirm", "proceed"],
        "weight": 1.1,
    },
    "reject": {
        "patterns": [
            r"^\s*(no|n|nope|reject|denied|deny|don't|do not)\b",
            r"\bi (reject|refuse|disagree)\b",
        ],
        "keywords": ["reject", "deny", "no", "refuse"],
        "weight": 1.1,
    },
    "query_status": {
        "patterns": [
            r"\bstatus\b",
            r"\bprogress\b",
            r"\bwhere are (we|you)\b",
            r"\bhow's it going\b",
            r"\bany update(s)?\b",
            r"\beta\b",
        ],
        "keywords": ["status", "progress", "update", "eta"],
        "weight": 1.0,
    },
}


@dataclass
class Intent:
    id: str = field(default_factory=lambda: f"INTENT-{uuid.uuid4().hex[:8]}")
    label: str = "unknown"
    confidence: float = 0.0
    slots: dict = field(default_factory=dict)
    text: str = ""
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class IntentClassifier:
    """Regex + keyword classifier for user intent."""

    def __init__(self, rules: Optional[dict] = None):
        self.rules = rules or INTENT_RULES

    def _score_label(self, text: str, lowered: str, label: str, spec: dict) -> tuple[float, dict]:
        score = 0.0
        slots: dict = {}
        for pattern in spec.get("patterns", []):
            match = re.search(pattern, lowered, flags=re.IGNORECASE)
            if match:
                score += 1.0
                slots.setdefault("matched_patterns", []).append(pattern)
        kw_hits = 0
        for kw in spec.get("keywords", []):
            if kw in lowered:
                kw_hits += 1
        if kw_hits:
            score += 0.5 * kw_hits
            slots["keyword_hits"] = kw_hits
        score *= spec.get("weight", 1.0)
        return score, slots

    def _extract_global_slots(self, text: str) -> dict:
        slots: dict = {}
        # Quoted phrases.
        quoted = re.findall(r'"([^"]+)"', text) + re.findall(r"'([^']+)'", text)
        if quoted:
            slots["quoted"] = quoted
        # Time mentions.
        time_match = re.search(
            r"\b(\d+)\s+(second|seconds|minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)\b",
            text,
            flags=re.IGNORECASE,
        )
        if time_match:
            slots["duration"] = {
                "value": int(time_match.group(1)),
                "unit": time_match.group(2).lower(),
            }
        # Capitalized noun phrases (very rough subject extraction).
        subjects = re.findall(r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*)\b", text)
        if subjects:
            slots["subjects"] = subjects[:5]
        return slots

    def classify(self, text: str) -> Intent:
        text = (text or "").strip()
        if not text:
            return Intent(label="unknown", confidence=0.0, text="")
        lowered = text.lower()
        results: list[tuple[str, float, dict]] = []
        for label, spec in self.rules.items():
            score, label_slots = self._score_label(text, lowered, label, spec)
            if score > 0:
                results.append((label, score, label_slots))
        if not results:
            slots = self._extract_global_slots(text)
            return Intent(label="unknown", confidence=0.1, slots=slots, text=text)
        results.sort(key=lambda r: r[1], reverse=True)
        best_label, best_score, best_slots = results[0]
        total = sum(r[1] for r in results)
        confidence = best_score / total if total > 0 else 0.0
        # Saturate via a soft cap.
        confidence = min(0.99, 0.3 + 0.7 * confidence)
        slots = self._extract_global_slots(text)
        slots.update(best_slots)
        if len(results) > 1:
            slots["alternatives"] = [
                {"label": l, "score": round(s, 3)} for l, s, _ in results[1:4]
            ]
        return Intent(
            label=best_label,
            confidence=round(confidence, 4),
            slots=slots,
            text=text,
        )

    def batch_classify(self, texts: list[str]) -> list[Intent]:
        return [self.classify(t) for t in texts]
