"""Command Enforcer — Enforce command execution policies"""
import re
from dataclasses import dataclass
from enum import Enum


class EnforcementAction(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REQUIRE_APPROVAL = "require_approval"
    DRY_RUN_ONLY = "dry_run_only"
    LOG_AND_ALLOW = "log_and_allow"


@dataclass
class EnforcementResult:
    action: EnforcementAction
    reason: str
    policy_name: str
    risk_score: int


class CommandEnforcer:
    """Enforce policies on command execution."""

    def __init__(self):
        self.blocked_patterns: list[tuple[str, str]] = [
            (r"rm\s+-rf\s+/", "Cannot delete root filesystem"),
            (r"mkfs\.", "Cannot format filesystems"),
            (r"dd\s+if=.*of=/dev/", "Cannot write to block devices"),
            (r":(){ :\|:& };:", "Fork bomb detected"),
            (r"chmod\s+-R\s+777\s+/", "Cannot chmod root"),
            (r"curl.*\|\s*(?:ba)?sh", "Piped script execution blocked"),
            (r"wget.*\|\s*(?:ba)?sh", "Piped script execution blocked"),
        ]

        self.approval_patterns: list[tuple[str, str]] = [
            (r"sudo\s+", "Sudo requires approval"),
            (r"docker\s+rm\s+", "Container removal requires approval"),
            (r"kubectl\s+delete\s+", "K8s resource deletion requires approval"),
            (r"git\s+push\s+--force", "Force push requires approval"),
            (r"git\s+reset\s+--hard", "Hard reset requires approval"),
            (r"DROP\s+TABLE", "DROP TABLE requires approval"),
            (r"DELETE\s+FROM", "DELETE requires approval"),
        ]

        self.log_patterns: list[tuple[str, str]] = [
            (r"pip\s+install\s+", "Package installation logged"),
            (r"npm\s+install\s+", "Package installation logged"),
            (r"apt\s+install\s+", "Package installation logged"),
        ]

    def enforce(self, command: str) -> EnforcementResult:
        cmd_lower = command.lower().strip()

        for pattern, reason in self.blocked_patterns:
            if re.search(pattern, cmd_lower):
                return EnforcementResult(
                    action=EnforcementAction.BLOCK,
                    reason=reason,
                    policy_name="blocked_commands",
                    risk_score=100,
                )

        for pattern, reason in self.approval_patterns:
            if re.search(pattern, cmd_lower):
                return EnforcementResult(
                    action=EnforcementAction.REQUIRE_APPROVAL,
                    reason=reason,
                    policy_name="approval_required",
                    risk_score=70,
                )

        for pattern, reason in self.log_patterns:
            if re.search(pattern, cmd_lower):
                return EnforcementResult(
                    action=EnforcementAction.LOG_AND_ALLOW,
                    reason=reason,
                    policy_name="logged_commands",
                    risk_score=20,
                )

        return EnforcementResult(
            action=EnforcementAction.ALLOW,
            reason="No policy matched — allowed",
            policy_name="default",
            risk_score=0,
        )

    def add_blocked_pattern(self, pattern: str, reason: str):
        self.blocked_patterns.append((pattern, reason))

    def add_approval_pattern(self, pattern: str, reason: str):
        self.approval_patterns.append((pattern, reason))
