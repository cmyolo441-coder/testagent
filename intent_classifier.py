"""IntentClassifier — keyword + regex based intent classification"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime, timezone
import re
import uuid


class IntentLabel(Enum):
    ASK_QUESTION = "ask_question"
    REQUEST_ACTION = "request_action"
    SET_GOAL = "set_goal"
    REQUEST_HELP = "request_help"
    GIVE_FEEDBACK = "give_feedback"
    CANCEL = "cancel"
    APPROVE = "approve"
    REJECT = "reject"
    QUERY_STATUS = "query_status"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    intent_id: str
    label: IntentLabel
    confidence: float
    slots: dict = field(default_factory=dict)
    raw_text: str = ""
    candidates: list[tuple[str, float]] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class IntentClassifier:
    """Classify user input into intent labels using keyword + regex heuristics."""

    QUESTION_REGEX = re.compile(
        r"^(what|when|where|who|why|how|which|is|are|do|does|did|can|could|should|would|will)\b",
        re.IGNORECASE,
    )
    HELP_REGEX = re.compile(r"\b(help|assist|stuck|don't know|dont know|how do i)\b", re.IGNORECASE)
    GOAL_REGEX = re.compile(
        r"\b(goal|objective|target|want to|need to|i want|i'd like|plan to|aim to)\b",
        re.IGNORECASE,
    )
    ACTION_REGEX = re.compile(
        r"^(please\s+)?(create|build|make|deploy|run|start|stop|restart|fix|write|generate|"
        r"send|open|close|delete|remove|update|install|configure|execute|launch)\b",
        re.IGNORECASE,
    )
    STATUS_REGEX = re.compile(
        r"\b(status|progress|update|how is|how's|where are we|state of|eta|done yet)\b",
        re.IGNORECASE,
    )
    CANCEL_REGEX = re.compile(
        r"\b(cancel|abort|stop it|nevermind|never mind|forget it|undo)\b",
        re.IGNORECASE,
    )
    APPROVE_REGEX = re.compile(
        r"^(yes|yep|yeah|sure|ok|okay|approve|approved|go ahead|sounds good|lgtm|confirmed)\b",
        re.IGNORECASE,
    )
    REJECT_REGEX = re.compile(
        r"^(no|nope|reject|rejected|decline|disagree|don't|do not)\b",
        re.IGNORECASE,
    )
    FEEDBACK_REGEX = re.compile(
        r"\b(feedback|i think|in my opinion|you should|you could|i feel|i noticed|"
        r"this is (good|bad|great|terrible|wrong|right))\b",
        re.IGNORECASE,
    )

    def __init__(self):
        self.rules: list[tuple[IntentLabel, re.Pattern, float]] = [
            (IntentLabel.CANCEL, self.CANCEL_REGEX, 0.92),
            (IntentLabel.APPROVE, self.APPROVE_REGEX, 0.9),
            (IntentLabel.REJECT, self.REJECT_REGEX, 0.9),
            (IntentLabel.QUERY_STATUS, self.STATUS_REGEX, 0.85),
            (IntentLabel.REQUEST_HELP, self.HELP_REGEX, 0.8),
            (IntentLabel.SET_GOAL, self.GOAL_REGEX, 0.78),
            (IntentLabel.REQUEST_ACTION, self.ACTION_REGEX, 0.82),
            (IntentLabel.GIVE_FEEDBACK, self.FEEDBACK_REGEX, 0.7),
            (IntentLabel.ASK_QUESTION, self.QUESTION_REGEX, 0.75),
        ]

    def classify(self, text: str) -> Intent:
        raw = text.strip()
        if not raw:
            return Intent(
                intent_id=f"INTENT-{uuid.uuid4().hex[:8]}",
                label=IntentLabel.UNKNOWN,
                confidence=0.0,
                raw_text=raw,
            )

        scores: dict[IntentLabel, float] = {}
        for label, pattern, base in self.rules:
            if pattern.search(raw):
                scores[label] = max(scores.get(label, 0.0), base)

        # Punctuation cues
        if raw.endswith("?"):
            scores[IntentLabel.ASK_QUESTION] = max(scores.get(IntentLabel.ASK_QUESTION, 0.0), 0.85)
        if raw.endswith("!"):
            scores[IntentLabel.REQUEST_ACTION] = max(
                scores.get(IntentLabel.REQUEST_ACTION, 0.0), scores.get(IntentLabel.REQUEST_ACTION, 0.0) + 0.05
            )

        if not scores:
            label = IntentLabel.UNKNOWN
            conf = 0.0
            candidates: list[tuple[str, float]] = []
        else:
            sorted_scores = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
            label, conf = sorted_scores[0]
            # Margin adjustment: shrink confidence when runner-up is close
            if len(sorted_scores) > 1:
                margin = sorted_scores[0][1] - sorted_scores[1][1]
                if margin < 0.1:
                    conf = max(0.4, conf - 0.1)
            candidates = [(lbl.value, round(sc, 4)) for lbl, sc in sorted_scores]

        slots = self._extract_slots(raw, label)

        return Intent(
            intent_id=f"INTENT-{uuid.uuid4().hex[:8]}",
            label=label,
            confidence=round(min(1.0, conf), 4),
            slots=slots,
            raw_text=raw,
            candidates=candidates,
        )

    def _extract_slots(self, text: str, label: IntentLabel) -> dict:
        slots: dict = {}
        # Target object: words after verbs
        m = re.search(
            r"\b(create|build|make|deploy|fix|write|generate|update|delete|remove|install)\s+"
            r"(?:a|an|the)?\s*([A-Za-z0-9_\-\s]{2,60})",
            text,
            re.IGNORECASE,
        )
        if m:
            slots["verb"] = m.group(1).lower()
            slots["object"] = m.group(2).strip().rstrip(".?!,")
        # Status target
        m = re.search(r"\bstatus of\s+([A-Za-z0-9_\-\s]{2,60})", text, re.IGNORECASE)
        if m:
            slots["target"] = m.group(1).strip().rstrip(".?!,")
        # Goal phrase
        m = re.search(
            r"\b(?:want to|need to|plan to|aim to|i'd like to|i want)\s+([^.?!]{3,120})",
            text,
            re.IGNORECASE,
        )
        if m:
            slots["goal"] = m.group(1).strip()
        # Question subject
        if label == IntentLabel.ASK_QUESTION:
            qm = re.search(r"^\s*(what|when|where|who|why|how|which)\b\s+(.+?)\??\s*$", text, re.IGNORECASE)
            if qm:
                slots["question_word"] = qm.group(1).lower()
                slots["question_body"] = qm.group(2).strip()
        return slots

    def explain(self, intent: Intent) -> str:
        if intent.label == IntentLabel.UNKNOWN:
            return f"No matching rules for: {intent.raw_text!r}"
        parts = [f"Label={intent.label.value} (conf={intent.confidence})"]
        if intent.slots:
            parts.append(f"slots={intent.slots}")
        if intent.candidates:
            parts.append(f"candidates={intent.candidates}")
        return " | ".join(parts)
