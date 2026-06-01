"""Goal Extractor — Extracts typed Goals from natural-language text."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional
import re
import uuid


GOAL_TRIGGERS = [
    r"\b(i want|i'd like|i would like|we want|we need|let's|lets)\s+to\s+(.+)$",
    r"\bgoal\s*[:=]\s*(.+)$",
    r"\bobjective\s*[:=]\s*(.+)$",
    r"\bmission\s*[:=]\s*(.+)$",
    r"^\s*(build|deploy|research|design|create|launch|ship|migrate|refactor|investigate)\s+(.+)$",
]

DURATION_PATTERN = re.compile(
    r"\b(?:in|within|by|over)\s+(\d+)\s+(second|seconds|minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)\b",
    re.IGNORECASE,
)

DEADLINE_PATTERN = re.compile(
    r"\b(?:by|before|due)\s+(\d{4}-\d{2}-\d{2})\b",
    re.IGNORECASE,
)

CRITERIA_TRIGGERS = re.compile(
    r"\b(?:so that|such that|so we can|in order to|with|including|that includes?)\s+(.+?)(?:\.|$)",
    re.IGNORECASE,
)

SCOPE_KEYWORDS: dict[str, list[str]] = {
    "research": ["research", "investigate", "study", "explore", "survey"],
    "build": ["build", "create", "implement", "develop", "code"],
    "deploy": ["deploy", "ship", "release", "launch", "rollout"],
    "design": ["design", "architect", "model", "draft"],
    "fix": ["fix", "patch", "repair", "debug", "resolve"],
    "ops": ["monitor", "operate", "maintain", "migrate", "upgrade"],
}

RISK_KEYWORDS: dict[str, list[str]] = {
    "high": ["production", "prod", "live", "critical", "security", "payment", "delete", "drop"],
    "medium": ["staging", "preview", "user-facing", "external"],
    "low": ["draft", "sandbox", "test", "experimental", "local", "dev"],
}

UNIT_TO_SECONDS = {
    "second": 1, "seconds": 1,
    "minute": 60, "minutes": 60,
    "hour": 3600, "hours": 3600,
    "day": 86400, "days": 86400,
    "week": 7 * 86400, "weeks": 7 * 86400,
    "month": 30 * 86400, "months": 30 * 86400,
    "year": 365 * 86400, "years": 365 * 86400,
}


@dataclass
class Goal:
    id: str = field(default_factory=lambda: f"GOAL-{uuid.uuid4().hex[:8]}")
    description: str = ""
    success_criteria: list[str] = field(default_factory=list)
    deadline: Optional[str] = None
    scope: str = "general"
    risk_hint: str = "low"
    source_text: str = ""
    extracted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GoalExtractor:
    """Extracts Goals from free-form text using regex heuristics."""

    def __init__(self, now_provider=None):
        self._now = now_provider or (lambda: datetime.now(timezone.utc))

    def _find_description(self, text: str) -> Optional[str]:
        for pattern in GOAL_TRIGGERS:
            match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
            if match:
                groups = [g for g in match.groups() if g]
                if groups:
                    desc = groups[-1].strip().rstrip(".")
                    # Strip trailing time clauses.
                    desc = DURATION_PATTERN.sub("", desc).strip()
                    desc = DEADLINE_PATTERN.sub("", desc).strip()
                    return desc.rstrip(",;.")
        return None

    def _find_deadline(self, text: str) -> Optional[str]:
        # Absolute date first.
        abs_match = DEADLINE_PATTERN.search(text)
        if abs_match:
            return abs_match.group(1)
        # Relative duration.
        dur_match = DURATION_PATTERN.search(text)
        if dur_match:
            value = int(dur_match.group(1))
            unit = dur_match.group(2).lower()
            seconds = UNIT_TO_SECONDS.get(unit, 0) * value
            if seconds > 0:
                deadline_dt = self._now() + timedelta(seconds=seconds)
                return deadline_dt.isoformat()
        return None

    def _find_success_criteria(self, text: str) -> list[str]:
        criteria: list[str] = []
        for match in CRITERIA_TRIGGERS.finditer(text):
            criterion = match.group(1).strip().rstrip(",;.")
            if criterion and len(criterion) < 200:
                criteria.append(criterion)
        # Bulleted criteria.
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("-", "*", "•")):
                bullet = stripped.lstrip("-*• ").strip()
                if bullet:
                    criteria.append(bullet)
        # Deduplicate while preserving order.
        seen: set[str] = set()
        unique: list[str] = []
        for c in criteria:
            key = c.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(c)
        return unique

    def _classify_scope(self, text: str) -> str:
        lowered = text.lower()
        best = "general"
        best_hits = 0
        for scope, words in SCOPE_KEYWORDS.items():
            hits = sum(1 for w in words if re.search(rf"\b{re.escape(w)}\b", lowered))
            if hits > best_hits:
                best_hits = hits
                best = scope
        return best

    def _classify_risk(self, text: str) -> str:
        lowered = text.lower()
        for level in ("high", "medium", "low"):
            for kw in RISK_KEYWORDS[level]:
                if re.search(rf"\b{re.escape(kw)}\b", lowered):
                    return level
        return "low"

    def extract(self, text: str) -> Optional[Goal]:
        text = (text or "").strip()
        if not text:
            return None
        description = self._find_description(text)
        if not description:
            # Heuristic fallback: imperative sentence?
            if re.match(r"^\s*[A-Z][a-z]+\s+\w+", text):
                description = text.split(".")[0].strip()
            else:
                return None
        return Goal(
            description=description,
            success_criteria=self._find_success_criteria(text),
            deadline=self._find_deadline(text),
            scope=self._classify_scope(text),
            risk_hint=self._classify_risk(text),
            source_text=text,
        )

    def extract_all(self, text: str) -> list[Goal]:
        if not text:
            return []
        goals: list[Goal] = []
        # Split on sentence-ish boundaries.
        chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
        for chunk in chunks:
            g = self.extract(chunk)
            if g:
                goals.append(g)
        # Always try the whole text as one as well, dedupe by description.
        whole = self.extract(text)
        if whole and not any(g.description == whole.description for g in goals):
            goals.append(whole)
        return goals
