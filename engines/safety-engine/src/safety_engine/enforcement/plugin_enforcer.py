"""Plugin Enforcer — Enforce policies on plugin execution"""
import re
from dataclasses import dataclass
from enum import Enum


class PluginAction(Enum):
    LOAD = "load"
    EXECUTE = "execute"
    CONFIGURE = "configure"
    UPDATE = "update"
    UNLOAD = "unload"
    NETWORK = "network"
    FILE_ACCESS = "file_access"


@dataclass
class PluginEnforcementResult:
    allowed: bool
    reason: str
    plugin_name: str
    action: PluginAction
    policy_name: str
    sandbox_required: bool = False
    audit_required: bool = False

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "plugin_name": self.plugin_name,
            "action": self.action.value,
            "policy_name": self.policy_name,
            "sandbox_required": self.sandbox_required,
            "audit_required": self.audit_required,
        }


class PluginEnforcer:
    """Enforce security policies on plugin execution."""

    BLOCKED_PLUGINS = {
        "malware-scanner": "Known malicious plugin",
        "keylogger": "Keylogging plugin blocked",
        "screen-capture": "Screen capture plugin blocked",
        "crypto-miner": "Cryptomining plugin blocked",
    }

    TRUSTED_PLUGINS = {
        "code-formatter": {"trust_level": "high", "permissions": ["file_access"]},
        "linter": {"trust_level": "high", "permissions": ["file_access"]},
        "test-runner": {"trust_level": "high", "permissions": ["file_access", "network"]},
        "git-integration": {"trust_level": "medium", "permissions": ["file_access", "network"]},
        "docker-integration": {"trust_level": "medium", "permissions": ["file_access", "network"]},
        "database-connector": {"trust_level": "medium", "permissions": ["network"]},
    }

    PLUGIN_ACTION_RISK = {
        PluginAction.LOAD: 30,
        PluginAction.EXECUTE: 50,
        PluginAction.CONFIGURE: 25,
        PluginAction.UPDATE: 35,
        PluginAction.UNLOAD: 10,
        PluginAction.NETWORK: 45,
        PluginAction.FILE_ACCESS: 40,
    }

    def __init__(self):
        self.custom_blocked: list[str] = []
        self.custom_trusted: dict[str, dict] = {}

    def enforce(self, plugin_name: str, action: PluginAction) -> PluginEnforcementResult:
        plugin_lower = plugin_name.lower().strip()

        for blocked, reason in self.BLOCKED_PLUGINS.items():
            if blocked.lower() in plugin_lower:
                return PluginEnforcementResult(
                    allowed=False,
                    reason=f"Blocked plugin: {reason}",
                    plugin_name=plugin_name,
                    action=action,
                    policy_name="plugin_blocklist",
                )

        if plugin_lower in self.custom_blocked:
            return PluginEnforcementResult(
                allowed=False,
                reason=f"Plugin in custom blocklist",
                plugin_name=plugin_name,
                action=action,
                policy_name="custom_blocklist",
            )

        trust_info = self.TRUSTED_PLUGINS.get(plugin_lower) or self.custom_trusted.get(plugin_lower)
        if trust_info:
            required_perms = self._get_required_permissions(action)
            allowed_perms = trust_info.get("permissions", [])

            has_perm = all(p in allowed_perms for p in required_perms)
            if not has_perm:
                missing = [p for p in required_perms if p not in allowed_perms]
                return PluginEnforcementResult(
                    allowed=False,
                    reason=f"Plugin lacks permissions: {', '.join(missing)}",
                    plugin_name=plugin_name,
                    action=action,
                    policy_name="permission_check",
                )

            return PluginEnforcementResult(
                allowed=True,
                reason=f"Trusted plugin ({trust_info['trust_level']})",
                plugin_name=plugin_name,
                action=action,
                policy_name="trusted_plugin",
                audit_required=action in (PluginAction.EXECUTE, PluginAction.NETWORK),
            )

        risk_score = self.PLUGIN_ACTION_RISK.get(action, 30)

        if action == PluginAction.NETWORK:
            return PluginEnforcementResult(
                allowed=True,
                reason="Untrusted plugin network access requires sandbox",
                plugin_name=plugin_name,
                action=action,
                policy_name="untrusted_network",
                sandbox_required=True,
                audit_required=True,
            )

        if action == PluginAction.EXECUTE:
            return PluginEnforcementResult(
                allowed=True,
                reason="Untrusted plugin execution requires sandbox",
                plugin_name=plugin_name,
                action=action,
                policy_name="untrusted_execute",
                sandbox_required=True,
                audit_required=True,
            )

        return PluginEnforcementResult(
            allowed=True,
            reason="Default allow with audit",
            plugin_name=plugin_name,
            action=action,
            policy_name="default_allow",
            audit_required=True,
        )

    def _get_required_permissions(self, action: PluginAction) -> list[str]:
        if action in (PluginAction.LOAD, PluginAction.UPDATE, PluginAction.UNLOAD):
            return []
        if action == PluginAction.NETWORK:
            return ["network"]
        if action in (PluginAction.EXECUTE, PluginAction.FILE_ACCESS):
            return ["file_access"]
        return []

    def add_blocked_plugin(self, name: str):
        self.custom_blocked.append(name.lower())

    def add_trusted_plugin(self, name: str, trust_level: str, permissions: list[str]):
        self.custom_trusted[name.lower()] = {
            "trust_level": trust_level,
            "permissions": permissions,
        }
