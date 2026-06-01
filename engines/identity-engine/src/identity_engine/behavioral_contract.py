"""Behavioral Contract — Rule-based action gating."""
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Union


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


WhenPattern = Union[str, re.Pattern, Callable[[dict], bool]]


@dataclass
class Rule:
    id: str = field(default_factory=lambda: f"RULE-{uuid.uuid4().hex[:8]}")
    when_pattern: Any = ".*"  # regex string, compiled regex, or callable(action) -> bool
    must: list[str] = field(default_factory=list)
    must_not: list[str] = field(default_factory=list)
    severity: str = "warn"  # info, warn, block, critical
    description: str = ""
    created_at: str = field(default_factory=_now_iso)

    def matches(self, action: dict) -> bool:
        target = action.get("description") or action.get("action") or action.get("tool") or ""
        pat = self.when_pattern
        if callable(pat):
            try:
                return bool(pat(action))
            except Exception:
                return False
        if isinstance(pat, re.Pattern):
            return bool(pat.search(str(target)))
        if isinstance(pat, str):
            try:
                return bool(re.search(pat, str(target)))
            except re.error:
                return pat in str(target)
        return False


@dataclass
class Violation:
    rule_id: str
    severity: str
    requirement: str  # the "must" or "must_not" clause violated
    kind: str  # "must" or "must_not"
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "requirement": self.requirement,
            "kind": self.kind,
            "description": self.description,
        }


@dataclass
class Verdict:
    allowed: bool
    violations: list[Violation] = field(default_factory=list)
    evaluated_rules: int = 0

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "violations": [v.to_dict() for v in self.violations],
            "evaluated_rules": self.evaluated_rules,
        }


class BehavioralContract:
    """A collection of rules evaluated against actions."""

    BLOCKING_SEVERITIES = {"block", "critical"}

    def __init__(self, rules: Optional[list[Rule]] = None):
        self.rules: list[Rule] = list(rules) if rules else []

    def add_rule(self, rule: Rule) -> str:
        self.rules.append(rule)
        return rule.id

    def remove_rule(self, rule_id: str) -> bool:
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.id != rule_id]
        return len(self.rules) != before

    def _action_tokens(self, action: dict) -> set[str]:
        parts: list[str] = []
        for k in ("description", "action", "tool", "intent", "summary"):
            val = action.get(k)
            if isinstance(val, str):
                parts.append(val)
        tags = action.get("tags") or []
        if isinstance(tags, list):
            parts.extend(str(t) for t in tags)
        text = " ".join(parts).lower()
        return {t.strip(".,;:!?") for t in text.split() if t.strip()}

    def evaluate(self, action: dict) -> Verdict:
        violations: list[Violation] = []
        evaluated = 0
        tokens = self._action_tokens(action)

        for rule in self.rules:
            if not rule.matches(action):
                continue
            evaluated += 1

            for requirement in rule.must:
                req_l = requirement.lower()
                if req_l not in tokens and req_l not in " ".join(tokens):
                    violations.append(Violation(
                        rule_id=rule.id,
                        severity=rule.severity,
                        requirement=requirement,
                        kind="must",
                        description=f"Action did not satisfy MUST '{requirement}'",
                    ))

            for forbidden in rule.must_not:
                forb_l = forbidden.lower()
                if forb_l in tokens or forb_l in " ".join(tokens):
                    violations.append(Violation(
                        rule_id=rule.id,
                        severity=rule.severity,
                        requirement=forbidden,
                        kind="must_not",
                        description=f"Action violated MUST_NOT '{forbidden}'",
                    ))

        allowed = not any(v.severity in self.BLOCKING_SEVERITIES for v in violations)
        return Verdict(allowed=allowed, violations=violations, evaluated_rules=evaluated)

    def to_dict(self) -> dict:
        return {
            "rules": [
                {
                    "id": r.id,
                    "when_pattern": r.when_pattern if isinstance(r.when_pattern, str) else "<callable_or_compiled>",
                    "must": list(r.must),
                    "must_not": list(r.must_not),
                    "severity": r.severity,
                    "description": r.description,
                    "created_at": r.created_at,
                }
                for r in self.rules
            ]
        }
