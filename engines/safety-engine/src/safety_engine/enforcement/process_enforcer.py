"""Process Enforcer — Enforce process execution policies"""
import re
import os
from dataclasses import dataclass
from enum import Enum


class ProcessAction(Enum):
    SPAWN = "spawn"
    SIGNAL = "signal"
    MODIFY = "modify"
    ATTACH = "attach"
    KILL = "kill"


@dataclass
class ProcessEnforcementResult:
    allowed: bool
    reason: str
    command: str
    action: ProcessAction
    policy_name: str
    requires_sandbox: bool = False

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "command": self.command,
            "action": self.action.value,
            "policy_name": self.policy_name,
            "requires_sandbox": self.requires_sandbox,
        }


class ProcessEnforcer:
    """Enforce process execution policies."""

    BLOCKED_COMMANDS = {
        r"init\b": "Cannot spawn init processes",
        r"systemctl\s+(?:start|stop|restart|enable|disable)": "Cannot modify system services",
        r"crontab\s+-[er]": "Cannot modify cron tables",
        r"at\s+": "Cannot schedule at jobs",
        r"nice\s+-n\s*-?\d+": "Cannot set process priority",
        r"renice\s+": "Cannot modify process priority",
        r"mount\s+.*-t\s+proc": "Cannot mount proc filesystem",
        r"ip\s+netns": "Cannot modify network namespaces",
    }

    PRIVILEGED_COMMANDS = {
        "sudo": 60, "su": 50, "pkexec": 60, "doas": 55,
    }

    SIGNAL_PATTERNS = {
        "kill": 40, "killall": 40, "pkill": 40,
        "kill -9": 60, "kill -SIGKILL": 60,
    }

    SAFE_COMMANDS = {
        "ls", "pwd", "echo", "cat", "head", "tail", "grep",
        "find", "wc", "sort", "uniq", "diff", "file",
        "python", "python3", "node", "ruby", "perl",
        "git", "npm", "pip",
    }

    def __init__(self):
        self.user = os.getenv("USER", "unknown")
        self.pid = os.getpid()

    def enforce(self, command: str) -> ProcessEnforcementResult:
        cmd_lower = command.lower().strip()

        for pattern, reason in self.BLOCKED_COMMANDS.items():
            if re.search(pattern, cmd_lower):
                return ProcessEnforcementResult(
                    allowed=False,
                    reason=reason,
                    command=command,
                    action=ProcessAction.SPAWN,
                    policy_name="blocked_command",
                )

        for signal_pattern, risk in self.SIGNAL_PATTERNS.items():
            if signal_pattern in cmd_lower:
                if self._is_own_process(cmd_lower):
                    return ProcessEnforcementResult(
                        allowed=False,
                        reason="Cannot signal own process tree",
                        command=command,
                        action=ProcessAction.SIGNAL,
                        policy_name="self_signal_block",
                    )
                return ProcessEnforcementResult(
                    allowed=True,
                    reason="Signal allowed with audit",
                    command=command,
                    action=ProcessAction.SIGNAL,
                    policy_name="signal_audit",
                )

        for pattern, risk in self.PRIVILEGED_COMMANDS.items():
            if pattern in cmd_lower:
                return ProcessEnforcementResult(
                    allowed=True,
                    reason=f"Privileged command: {pattern}",
                    command=command,
                    action=ProcessAction.SPAWN,
                    policy_name="privileged_command",
                    requires_sandbox=True,
                )

        if "&&" in cmd_lower and cmd_lower.count("&&") > 3:
            return ProcessEnforcementResult(
                allowed=True,
                reason="Complex command chain",
                command=command,
                action=ProcessAction.SPAWN,
                policy_name="complex_chain",
                requires_sandbox=True,
            )

        base_cmd = cmd_lower.split()[0] if cmd_lower.split() else ""
        if base_cmd in self.SAFE_COMMANDS:
            return ProcessEnforcementResult(
                allowed=True,
                reason="Safe command",
                command=command,
                action=ProcessAction.SPAWN,
                policy_name="safe_command",
            )

        if "&" in cmd_lower or "nohup" in cmd_lower or "screen" in cmd_lower or "tmux" in cmd_lower:
            return ProcessEnforcementResult(
                allowed=True,
                reason="Background process",
                command=command,
                action=ProcessAction.SPAWN,
                policy_name="background_process",
                requires_sandbox=True,
            )

        return ProcessEnforcementResult(
            allowed=True,
            reason="Default allow",
            command=command,
            action=ProcessAction.SPAWN,
            policy_name="default_allow",
        )

    def _is_own_process(self, command: str) -> bool:
        pid_match = re.search(r"kill\s+(?:-9\s+)?(\d+)", command)
        if pid_match:
            target_pid = int(pid_match.group(1))
            return target_pid == self.pid
        return False
