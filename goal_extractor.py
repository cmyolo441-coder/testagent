"""GoalExtractor — extract structured Goal objects from free text"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime, timezone, timedelta
import re
import uuid


class GoalScope(Enum):
    PERSONAL = "personal"
    TEAM = "team"
    PROJECT = "project"
    ORG = "org"
    GLOBAL = "global"
    UNKNOWN = "unknown"


class RiskHint(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


@dataclass
class Goal:
    goal_id: str
    description: str
    success_criteria: list[str] = field(default_factory=list)
    deadline_hint: Optional[str] = None
    scope: GoalScope = GoalScope.UNKNOWN
    risk_hint: RiskHint = RiskHint.UNKNOWN
    verbs: list[str] = field(default_factory=list)
    raw_text: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class GoalExtractor:
    """Extract structured Goal(description, success_criteria, deadline_hint, scope, risk_hint)."""

    ACTION_VERBS = {
        "build", "deploy", "research", "design", "launch", "ship", "create",
        "implement", "investigate", "develop", "deliver", "produce", "write",
        "publish", "scale", "migrate", "refactor", "optimize", "analyze",
    }
    GOAL_TRIGGER_REGEX = re.compile(
        r"\b(goal|objective|target|mission|want to|need to|plan to|aim to|"
        r"i want|i'd like to|let's|lets|we should|we must|i need to|build a|"
        r"deploy|research|launch)\b",
        re.IGNORECASE,
    )
    DESCRIPTION_REGEX = re.compile(
        r"\b(?:build|deploy|research|design|launch|ship|create|implement|develop|deliver|"
        r"produce|write|publish|scale|migrate|refactor|optimize|analyze)\s+"
        r"(?:a|an|the)?\s*([A-Za-z0-9_\-][^.?!\n]{2,160})",
        re.IGNORECASE,
    )
    DURATION_REGEX = re.compile(
        r"\bin\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)\b",
        re.IGNORECASE,
    )
    BY_DATE_REGEX = re.compile(
        r"\bby\s+([A-Za-z]+\s+\d{1,2}(?:,\s*\d{4})?|\d{4}-\d{2}-\d{2}|next\s+(?:week|month|quarter|year)|"
        r"(?:end of|eo[wmqy])\s+(?:week|month|quarter|year|day))",
        re.IGNORECASE,
    )
    SUCCESS_REGEX = re.compile(
        r"\b(?:success|done|complete|achieved|finished)\s+(?:when|if|means)\s+([^.?!\n]{3,160})",
        re.IGNORECASE,
    )
    METRIC_REGEX = re.compile(
        r"\b(\d+(?:\.\d+)?%|\d+\s*(?:users|customers|requests|qps|rps|ms|s|minutes|hours|reqs))\b",
        re.IGNORECASE,
    )

    SCOPE_KEYWORDS = {
        GoalScope.PERSONAL: {"i ", "me ", "my ", "myself"},
        GoalScope.TEAM: {"team", "our team", "we ", "us "},
        GoalScope.PROJECT: {"project", "product", "feature", "release"},
        GoalScope.ORG: {"company", "organization", "org ", "enterprise"},
        GoalScope.GLOBAL: {"industry", "everyone", "world", "global"},
    }
    HIGH_RISK_KEYWORDS = {"production", "critical", "irreversible", "compliance", "security", "money", "payment"}
    MEDIUM_RISK_KEYWORDS = {"deploy", "migrate", "delete", "remove", "schema", "database"}

    def extract(self, text: str) -> Optional[Goal]:
        raw = text.strip()
        if not raw:
            return None
        if not self.GOAL_TRIGGER_REGEX.search(raw):
            # Allow if there is at least an action verb at the start
            first_word = re.match(r"\s*([A-Za-z]+)", raw)
            if not (first_word and first_word.group(1).lower() in self.ACTION_VERBS):
                return None

        description = self._extract_description(raw)
        deadline = self._extract_deadline(raw)
        criteria = self._extract_success_criteria(raw)
        scope = self._infer_scope(raw)
        risk = self._infer_risk(raw)
        verbs = self._extract_verbs(raw)

        return Goal(
            goal_id=f"GOAL-{uuid.uuid4().hex[:8]}",
            description=description,
            success_criteria=criteria,
            deadline_hint=deadline,
            scope=scope,
            risk_hint=risk,
            verbs=verbs,
            raw_text=raw,
        )

    def _extract_description(self, text: str) -> str:
        m = self.DESCRIPTION_REGEX.search(text)
        if m:
            verb = m.group(0).split()[0].lower()
            object_part = m.group(1).strip().rstrip(".?!,;:")
            return f"{verb} {object_part}".strip()
        # Fallback: trim trigger phrase
        m2 = re.search(
            r"\b(?:want to|need to|plan to|aim to|i'd like to|i want|let's|lets|we should|we must|i need to)\s+([^.?!\n]{3,200})",
            text,
            re.IGNORECASE,
        )
        if m2:
            return m2.group(1).strip().rstrip(".?!,;:")
        return text[:200].strip()

    def _extract_deadline(self, text: str) -> Optional[str]:
        m = self.DURATION_REGEX.search(text)
        if m:
            qty = int(m.group(1))
            unit = m.group(2).lower()
            days_map = {
                "day": 1, "days": 1,
                "week": 7, "weeks": 7,
                "month": 30, "months": 30,
                "year": 365, "years": 365,
            }
            days = qty * days_map[unit]
            est = datetime.now(timezone.utc) + timedelta(days=days)
            return f"in {qty} {unit} (~{est.date().isoformat()})"
        m = self.BY_DATE_REGEX.search(text)
        if m:
            return f"by {m.group(1).strip()}"
        if re.search(r"\b(asap|immediately|right now|today)\b", text, re.IGNORECASE):
            return "asap"
        return None

    def _extract_success_criteria(self, text: str) -> list[str]:
        criteria: list[str] = []
        for m in self.SUCCESS_REGEX.finditer(text):
            criteria.append(m.group(1).strip().rstrip(".?!,;:"))
        for m in self.METRIC_REGEX.finditer(text):
            metric = m.group(1).strip()
            if metric not in criteria:
                criteria.append(f"metric:{metric}")
        # Bullet-style 'must', 'should'
        for m in re.finditer(r"\b(?:must|should|needs to)\s+([^.?!\n]{3,160})", text, re.IGNORECASE):
            criteria.append(m.group(1).strip().rstrip(".?!,;:"))
        # De-dupe while preserving order
        seen = set()
        out = []
        for c in criteria:
            key = c.lower()
            if key not in seen:
                seen.add(key)
                out.append(c)
        return out

    def _infer_scope(self, text: str) -> GoalScope:
        lowered = " " + text.lower() + " "
        best = GoalScope.UNKNOWN
        best_hits = 0
        for scope, kws in self.SCOPE_KEYWORDS.items():
            hits = sum(1 for kw in kws if kw in lowered)
            if hits > best_hits:
                best_hits = hits
                best = scope
        return best

    def _infer_risk(self, text: str) -> RiskHint:
        lowered = text.lower()
        if any(kw in lowered for kw in self.HIGH_RISK_KEYWORDS):
            return RiskHint.HIGH
        if any(kw in lowered for kw in self.MEDIUM_RISK_KEYWORDS):
            return RiskHint.MEDIUM
        if any(kw in lowered for kw in {"experiment", "draft", "prototype", "sandbox"}):
            return RiskHint.LOW
        return RiskHint.UNKNOWN

    def _extract_verbs(self, text: str) -> list[str]:
        words = re.findall(r"[A-Za-z']+", text.lower())
        return sorted({w for w in words if w in self.ACTION_VERBS})
