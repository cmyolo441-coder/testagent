"""Institutional Memory — Organizational policies, norms, and procedures"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class Policy:
    id: str = field(default_factory=lambda: f"POL-{uuid.uuid4().hex[:12]}")
    title: str = ""
    description: str = ""
    policy_type: str = ""  # security, operational, ethical, compliance, protocol
    scope: str = "global"  # global, team, project, mission
    severity: str = "medium"  # low, medium, high, critical
    rules: list[str] = field(default_factory=list)
    exceptions: list[str] = field(default_factory=list)
    related_policies: list[str] = field(default_factory=list)
    approved_by: Optional[str] = None
    effective_date: Optional[str] = None
    expires_date: Optional[str] = None
    is_active: bool = True
    tags: list[str] = field(default_factory=list)
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "policy_type": self.policy_type,
            "scope": self.scope,
            "severity": self.severity,
            "is_active": self.is_active,
            "version": self.version,
            "tags": self.tags,
            "created_at": self.created_at,
        }


class InstitutionalMemory:
    """Manages organizational policies and institutional knowledge."""

    def __init__(self, store=None):
        self.store = store
        self.policies: dict[str, Policy] = {}
        self._type_index: dict[str, list[str]] = {}

    def store_policy(self, title: str, description: str = "",
                     policy_type: str = "operational", scope: str = "global",
                     severity: str = "medium", rules: list[str] = None,
                     exceptions: list[str] = None, approved_by: str = None,
                     tags: list[str] = None) -> Policy:
        policy = Policy(
            title=title,
            description=description,
            policy_type=policy_type,
            scope=scope,
            severity=severity,
            rules=rules or [],
            exceptions=exceptions or [],
            approved_by=approved_by,
            tags=tags or [],
        )
        self.policies[policy.id] = policy

        if policy_type not in self._type_index:
            self._type_index[policy_type] = []
        self._type_index[policy_type].append(policy.id)

        if self.store:
            from memory_engine.stores.sqlite_store import MemoryRecord
            record = MemoryRecord(
                memory_type="institutional",
                content=f"Policy: {title} ({policy_type}/{severity})",
                context={"policy_type": policy_type, "scope": scope, "severity": severity},
                importance=0.8 if severity in ("high", "critical") else 0.5,
                tags=tags or [],
                metadata={"policy_id": policy.id},
            )
            self.store.store(record)

        return policy

    def get_policies(self, policy_type: str = None, scope: str = None,
                     active_only: bool = True) -> list[Policy]:
        results = list(self.policies.values())
        if active_only:
            results = [p for p in results if p.is_active]
        if policy_type:
            results = [p for p in results if p.policy_type == policy_type]
        if scope:
            results = [p for p in results if p.scope == scope or p.scope == "global"]
        return results

    def get_policy(self, policy_id: str) -> Optional[Policy]:
        return self.policies.get(policy_id)

    def update_policy(self, policy_id: str, **kwargs) -> Optional[Policy]:
        policy = self.policies.get(policy_id)
        if not policy:
            return None
        for key, value in kwargs.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        policy.version += 1
        policy.updated_at = datetime.now(timezone.utc).isoformat()
        return policy

    def deactivate_policy(self, policy_id: str) -> bool:
        policy = self.policies.get(policy_id)
        if not policy:
            return False
        policy.is_active = False
        policy.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def check_compliance(self, action: str, context: dict = None) -> list[dict]:
        violations = []
        for policy in self.get_policies():
            for rule in policy.rules:
                if self._rule_conflicts_with_action(rule, action):
                    violations.append({
                        "policy_id": policy.id,
                        "policy_title": policy.title,
                        "rule": rule,
                        "severity": policy.severity,
                        "action": action,
                    })
        return violations

    def _rule_conflicts_with_action(self, rule: str, action: str) -> bool:
        rule_lower = rule.lower()
        action_lower = action.lower()
        if "never" in rule_lower:
            forbidden = rule_lower.split("never")[-1].strip()
            return forbidden in action_lower
        if "must" in rule_lower:
            required = rule_lower.split("must")[-1].strip()
            return required not in action_lower
        return False

    def get_applicable_policies(self, scope: str, tags: list[str] = None) -> list[Policy]:
        results = [
            p for p in self.policies.values()
            if p.is_active and (p.scope == "global" or p.scope == scope)
        ]
        if tags:
            tag_set = set(tags)
            results = [p for p in results if tag_set & set(p.tags)]
        return results

    def get_stats(self) -> dict:
        policies = list(self.policies.values())
        active = [p for p in policies if p.is_active]
        by_type = {}
        for p in policies:
            by_type[p.policy_type] = by_type.get(p.policy_type, 0) + 1
        return {
            "total_policies": len(policies),
            "active_policies": len(active),
            "by_type": by_type,
        }
