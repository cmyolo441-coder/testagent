"""Risk Policy — Risk-based access control for tool execution"""
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(Enum):
    SAFE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class PolicyAction(Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    REQUIRE_SANDBOX = "require_sandbox"
    LOG_AND_ALLOW = "log_and_allow"


@dataclass
class RiskPolicyRule:
    name: str
    max_risk_score: int = 100
    action: PolicyAction = PolicyAction.ALLOW
    require_sandbox: bool = False
    require_approval_above: int = 60
    timeout_multiplier: float = 1.0
    allowed_tools: list[str] = field(default_factory=list)
    blocked_tools: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class RiskAssessment:
    score: int
    level: RiskLevel
    action: PolicyAction
    requires_sandbox: bool
    requires_approval: bool
    rule_name: str
    reasons: list[str]

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "level": self.level.name,
            "action": self.action.value,
            "requires_sandbox": self.requires_sandbox,
            "requires_approval": self.requires_approval,
            "rule_name": self.rule_name,
            "reasons": self.reasons,
        }


class RiskPolicy:
    """Risk-based access control for tool execution."""

    TOOL_RISK_SCORES = {
        "read_file": 10, "list_directory": 5, "write_file": 30,
        "delete_file": 50, "execute_command": 40, "run_python": 35,
        "git_commit": 20, "git_push": 45, "git_force_push": 70,
        "deploy": 60, "rollback": 40,
        "database_query": 25, "database_delete": 65,
        "send_email": 35, "cloud_deploy": 55,
        "browser_open": 30, "browser_click": 25,
        "install_package": 35, "uninstall_package": 30,
        "ssh_command": 40, "docker_run": 45,
    }

    def __init__(self):
        self.rules: list[RiskPolicyRule] = []
        self._setup_default_rules()

    def _setup_default_rules(self):
        self.rules = [
            RiskPolicyRule(
                name="safe_operations",
                max_risk_score=30,
                action=PolicyAction.ALLOW,
                require_sandbox=False,
                require_approval_above=100,
            ),
            RiskPolicyRule(
                name="standard_operations",
                max_risk_score=60,
                action=PolicyAction.ALLOW,
                require_sandbox=False,
                require_approval_above=60,
            ),
            RiskPolicyRule(
                name="elevated_operations",
                max_risk_score=80,
                action=PolicyAction.REQUIRE_APPROVAL,
                require_sandbox=False,
                require_approval_above=40,
            ),
            RiskPolicyRule(
                name="dangerous_operations",
                max_risk_score=100,
                action=PolicyAction.REQUIRE_SANDBOX,
                require_sandbox=True,
                require_approval_above=20,
            ),
        ]

    def check(self, tool_call: dict) -> RiskAssessment:
        tool_name = tool_call.get("tool_name", "")
        arguments = tool_call.get("arguments", {})
        context = tool_call.get("context", {})

        score = self._calculate_risk_score(tool_name, arguments, context)
        level = self._score_to_level(score)
        reasons = self._get_reasons(tool_name, arguments, score)

        matching_rule = self._find_matching_rule(score, tool_name)

        if matching_rule:
            action = matching_rule.action
            requires_sandbox = matching_rule.require_sandbox
            requires_approval = score >= matching_rule.require_approval_above
            rule_name = matching_rule.name
        else:
            action = PolicyAction.DENY
            requires_sandbox = True
            requires_approval = True
            rule_name = "no_matching_rule"

        if score >= 95:
            action = PolicyAction.DENY
            reasons.append("Risk score exceeds maximum threshold")

        return RiskAssessment(
            score=score,
            level=level,
            action=action,
            requires_sandbox=requires_sandbox,
            requires_approval=requires_approval,
            rule_name=rule_name,
            reasons=reasons,
        )

    def add_rule(self, rule: RiskPolicyRule):
        self.rules.append(rule)

    def set_tool_risk(self, tool_name: str, score: int):
        self.TOOL_RISK_SCORES[tool_name] = score

    def _calculate_risk_score(self, tool_name: str, arguments: dict, context: dict) -> int:
        base_score = self.TOOL_RISK_SCORES.get(tool_name, 30)

        if arguments:
            arg_str = str(arguments).lower()
            if any(w in arg_str for w in ["rm -rf", "drop table", "delete from"]):
                base_score = max(base_score, 80)
            if any(w in arg_str for w in ["/etc", "/usr", "/root"]):
                base_score = max(base_score, 70)
            if "sudo" in arg_str:
                base_score = max(base_score, 65)

        role = context.get("role", "agent")
        if role == "admin":
            base_score = max(0, base_score - 10)
        elif role == "viewer":
            base_score = max(0, base_score - 20)

        risk_multiplier = context.get("risk_multiplier", 1.0)
        base_score = int(base_score * risk_multiplier)

        return min(100, max(0, base_score))

    def _find_matching_rule(self, score: int, tool_name: str) -> RiskPolicyRule | None:
        for rule in self.rules:
            if tool_name in rule.blocked_tools:
                continue
            if rule.allowed_tools and tool_name not in rule.allowed_tools:
                continue
            if score <= rule.max_risk_score:
                return rule
        return None

    def _get_reasons(self, tool_name: str, arguments: dict, score: int) -> list[str]:
        reasons = []
        if tool_name in self.TOOL_RISK_SCORES:
            reasons.append(f"Tool base risk: {self.TOOL_RISK_SCORES[tool_name]}")
        if score >= 60:
            reasons.append("Elevated risk score")
        if score >= 80:
            reasons.append("High risk operation")
        return reasons

    def _score_to_level(self, score: int) -> RiskLevel:
        if score >= 80:
            return RiskLevel.CRITICAL
        if score >= 60:
            return RiskLevel.HIGH
        if score >= 40:
            return RiskLevel.MEDIUM
        if score >= 20:
            return RiskLevel.LOW
        return RiskLevel.SAFE
