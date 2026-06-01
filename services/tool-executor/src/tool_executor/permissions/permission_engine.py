"""Permission Engine — Fine-grained tool access control"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Permission(Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"
    NETWORK = "network"
    DEPLOY = "deploy"


@dataclass
class Policy:
    name: str
    permissions: list[Permission]
    allowed_tools: list[str] = field(default_factory=list)
    denied_tools: list[str] = field(default_factory=list)
    max_risk_score: int = 100
    require_approval_above: int = 60
    sandbox_required: bool = False


@dataclass
class AccessDecision:
    allowed: bool
    reason: str
    policy_name: str
    requires_approval: bool = False
    sandbox_required: bool = False


class PermissionEngine:
    """Enforce tool access policies."""

    def __init__(self):
        self.policies: dict[str, Policy] = {}
        self.role_policies: dict[str, list[str]] = {}
        self._setup_default_policies()

    def _setup_default_policies(self):
        self.add_policy(Policy(
            name="readonly",
            permissions=[Permission.READ],
            max_risk_score=30,
            require_approval_above=100,
        ))
        self.add_policy(Policy(
            name="standard",
            permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE],
            max_risk_score=60,
            require_approval_above=60,
        ))
        self.add_policy(Policy(
            name="elevated",
            permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.DELETE, Permission.NETWORK],
            max_risk_score=80,
            require_approval_above=40,
        ))
        self.add_policy(Policy(
            name="admin",
            permissions=list(Permission),
            max_risk_score=100,
            require_approval_above=80,
        ))
        self.role_policies["agent"] = ["standard"]
        self.role_policies["admin"] = ["admin"]
        self.role_policies["viewer"] = ["readonly"]

    def add_policy(self, policy: Policy):
        self.policies[policy.name] = policy

    def check_access(self, role: str, tool_name: str, risk_score: int = 0) -> AccessDecision:
        policy_names = self.role_policies.get(role, ["standard"])
        for pname in policy_names:
            policy = self.policies.get(pname)
            if not policy:
                continue

            if tool_name in policy.denied_tools:
                return AccessDecision(
                    allowed=False,
                    reason=f"Tool explicitly denied by policy: {pname}",
                    policy_name=pname,
                )

            if policy.allowed_tools and tool_name not in policy.allowed_tools:
                continue

            if risk_score > policy.max_risk_score:
                return AccessDecision(
                    allowed=False,
                    reason=f"Risk score {risk_score} exceeds policy max {policy.max_risk_score}",
                    policy_name=pname,
                )

            requires_approval = risk_score >= policy.require_approval_above
            return AccessDecision(
                allowed=True,
                reason="Access granted",
                policy_name=pname,
                requires_approval=requires_approval,
                sandbox_required=policy.sandbox_required,
            )

        return AccessDecision(
            allowed=False,
            reason="No matching policy found",
            policy_name="none",
        )

    def get_role_policies(self, role: str) -> list[str]:
        return self.role_policies.get(role, [])
