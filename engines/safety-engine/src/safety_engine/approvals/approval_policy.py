"""Approval Policy — Define when approvals are required"""
from dataclasses import dataclass
from enum import Enum
from safety_engine.risk.risk_model import RiskLevel


class ApprovalRequirement(Enum):
    AUTO_APPROVE = "auto_approve"
    AUTO_APPROVE_LOW_RISK = "auto_approve_low_risk"
    USER_APPROVAL = "user_approval"
    ADMIN_APPROVAL = "admin_approval"
    MULTI_APPROVAL = "multi_approval"
    BLOCK = "block"


@dataclass
class PolicyRule:
    risk_level: RiskLevel
    action_type: str
    requirement: ApprovalRequirement
    max_auto_score: int = 30
    approvers_needed: int = 1
    timeout_seconds: int = 300
    description: str = ""


@dataclass
class ApprovalDecision:
    requirement: ApprovalRequirement
    reason: str
    approvers_needed: int
    timeout_seconds: int
    policy_name: str

    def to_dict(self) -> dict:
        return {
            "requirement": self.requirement.value,
            "reason": self.reason,
            "approvers_needed": self.approvers_needed,
            "timeout_seconds": self.timeout_seconds,
            "policy_name": self.policy_name,
        }


class ApprovalPolicy:
    """Determine approval requirements based on risk level and action type."""

    def __init__(self):
        self.rules: list[PolicyRule] = []
        self.action_overrides: dict[str, ApprovalRequirement] = {}
        self._setup_default_rules()

    def _setup_default_rules(self):
        self.rules = [
            PolicyRule(
                risk_level=RiskLevel.SAFE,
                action_type="*",
                requirement=ApprovalRequirement.AUTO_APPROVE,
                max_auto_score=15,
                description="Safe actions auto-approved",
            ),
            PolicyRule(
                risk_level=RiskLevel.LOW,
                action_type="*",
                requirement=ApprovalRequirement.AUTO_APPROVE_LOW_RISK,
                max_auto_score=30,
                description="Low risk auto-approved",
            ),
            PolicyRule(
                risk_level=RiskLevel.MEDIUM,
                action_type="*",
                requirement=ApprovalRequirement.USER_APPROVAL,
                timeout_seconds=300,
                description="Medium risk requires user approval",
            ),
            PolicyRule(
                risk_level=RiskLevel.HIGH,
                action_type="*",
                requirement=ApprovalRequirement.ADMIN_APPROVAL,
                timeout_seconds=120,
                description="High risk requires admin approval",
            ),
            PolicyRule(
                risk_level=RiskLevel.CRITICAL,
                action_type="*",
                requirement=ApprovalRequirement.BLOCK,
                description="Critical risk actions blocked",
            ),
        ]

        self.action_overrides = {
            "sudo": ApprovalRequirement.ADMIN_APPROVAL,
            "rm -rf": ApprovalRequirement.BLOCK,
            "mkfs": ApprovalRequirement.BLOCK,
            "DROP TABLE": ApprovalRequirement.ADMIN_APPROVAL,
            "DELETE FROM": ApprovalRequirement.ADMIN_APPROVAL,
            "git push --force": ApprovalRequirement.MULTI_APPROVAL,
            "deploy": ApprovalRequirement.MULTI_APPROVAL,
        }

    def check(self, risk_level: RiskLevel, action_type: str,
              risk_score: int = 0) -> ApprovalDecision:
        override = self._find_override(action_type)
        if override:
            return ApprovalDecision(
                requirement=override,
                reason=f"Action '{action_type}' has explicit override",
                approvers_needed=self._get_approvers_needed(override),
                timeout_seconds=self._get_timeout(override),
                policy_name="action_override",
            )

        rule = self._find_rule(risk_level, action_type)
        if rule:
            if rule.requirement == ApprovalRequirement.AUTO_APPROVE_LOW_RISK:
                if risk_score <= rule.max_auto_score:
                    return ApprovalDecision(
                        requirement=ApprovalRequirement.AUTO_APPROVE,
                        reason=f"Score {risk_score} below auto-approve threshold {rule.max_auto_score}",
                        approvers_needed=0,
                        timeout_seconds=0,
                        policy_name=rule.description,
                    )

            return ApprovalDecision(
                requirement=rule.requirement,
                reason=rule.description,
                approvers_needed=rule.approvers_needed,
                timeout_seconds=rule.timeout_seconds,
                policy_name=rule.description,
            )

        return ApprovalDecision(
            requirement=ApprovalRequirement.USER_APPROVAL,
            reason="No matching policy, defaulting to user approval",
            approvers_needed=1,
            timeout_seconds=300,
            policy_name="default",
        )

    def _find_override(self, action_type: str) -> ApprovalRequirement | None:
        action_lower = action_type.lower()
        for pattern, req in self.action_overrides.items():
            if pattern.lower() in action_lower:
                return req
        return None

    def _find_rule(self, risk_level: RiskLevel, action_type: str) -> PolicyRule | None:
        for rule in self.rules:
            if rule.risk_level == risk_level:
                if rule.action_type == "*" or action_type.lower() in rule.action_type.lower():
                    return rule
        return None

    def _get_approvers_needed(self, req: ApprovalRequirement) -> int:
        if req == ApprovalRequirement.MULTI_APPROVAL:
            return 2
        if req in (ApprovalRequirement.USER_APPROVAL, ApprovalRequirement.ADMIN_APPROVAL):
            return 1
        return 0

    def _get_timeout(self, req: ApprovalRequirement) -> int:
        if req == ApprovalRequirement.BLOCK:
            return 0
        if req == ApprovalRequirement.ADMIN_APPROVAL:
            return 120
        return 300

    def add_override(self, action_pattern: str, requirement: ApprovalRequirement):
        self.action_overrides[action_pattern] = requirement

    def add_rule(self, rule: PolicyRule):
        self.rules.append(rule)
