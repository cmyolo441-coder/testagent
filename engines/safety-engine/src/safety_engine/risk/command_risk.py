"""Command Risk — Assess risk of shell commands"""
import re
from dataclasses import dataclass
from safety_engine.risk.risk_model import RiskLevel, RiskAssessment


@dataclass
class CommandRiskAssessment:
    command: str
    score: int
    level: RiskLevel
    reasons: list[str]
    blocked: bool
    requires_approval: bool
    sandbox_recommended: bool
    destructive_ops: list[str]

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "score": self.score,
            "level": self.level.name,
            "reasons": self.reasons,
            "blocked": self.blocked,
            "requires_approval": self.requires_approval,
            "sandbox_recommended": self.sandbox_recommended,
            "destructive_ops": self.destructive_ops,
        }


class CommandRisk:
    """Assess risk of shell commands with granular analysis."""

    DESTRUCTIVE_COMMANDS = {
        "rm": 40, "rm -rf": 85, "rm -r": 70, "rm -f": 35,
        "rmdir": 25, "shred": 90,
        "mkfs": 100, "mkfs.ext4": 100, "mkfs.xfs": 100,
        "dd": 90, "dd if=/dev/zero": 95,
        "format": 100, "fdisk": 80, "parted": 80, "sgdisk": 80,
        "chmod": 30, "chmod -R 777": 60, "chmod +s": 80,
        "chown": 40, "chown -R": 55,
        "sudo": 60, "su": 50, "sudo rm": 85,
        "passwd": 70, "useradd": 50, "userdel": 60,
        "kill": 40, "kill -9": 60, "pkill": 40, "killall": 45,
        "shutdown": 50, "reboot": 50, "halt": 50, "poweroff": 50,
        "mount": 40, "umount": 40, "mount --bind": 35,
        "iptables": 60, "iptables -F": 80, "nft": 60,
        "systemctl stop": 50, "systemctl disable": 60,
    }

    NETWORK_RISK_COMMANDS = {
        "curl": 20, "wget": 20, "nc": 35, "ncat": 35,
        "netcat": 35, "telnet": 30, "ssh": 30, "scp": 30,
        "rsync": 20, "rsync -avz": 25,
        "nc -l": 45, "nc -e": 60,
        "python -m http.server": 30,
        "nmap": 50, "masscan": 55,
    }

    PRIVILEGE_ESCALATION = {
        "sudo": 60, "sudo -i": 70, "sudo -s": 65,
        "su -": 55, "su root": 60,
        "pkexec": 60, "doas": 55,
        "chmod +s": 80, "chmod u+s": 80,
        "setcap": 70,
    }

    SAFE_COMMANDS = {
        "ls", "pwd", "echo", "cat", "head", "tail", "wc",
        "sort", "uniq", "diff", "file", "which", "type",
        "git status", "git log", "git diff", "git show",
        "python --version", "python3 --version",
        "node --version", "npm --version",
        "docker ps", "docker images", "docker logs",
        "kubectl get", "kubectl describe",
    }

    SYSTEM_PATHS = [
        "/etc", "/usr", "/bin", "/sbin", "/boot", "/root",
        "/var/log", "/proc", "/sys", "/dev", "/lib", "/lib64",
        "/opt", "/srv",
    ]

    def assess_command_risk(self, command: str) -> CommandRiskAssessment:
        score = 0
        reasons: list[str] = []
        destructive_ops: list[str] = []
        blocked = False

        cmd = command.strip()
        cmd_lower = cmd.lower()

        for pattern, risk in self.DESTRUCTIVE_COMMANDS.items():
            if pattern in cmd_lower:
                score = max(score, risk)
                reasons.append(f"Destructive command: {pattern}")
                destructive_ops.append(pattern)

        if any(cmd_lower.startswith(safe) for safe in self.SAFE_COMMANDS):
            score = max(0, score - 25)
            reasons.append("Safe base command")

        for pattern, risk in self.PRIVILEGE_ESCALATION.items():
            if pattern in cmd_lower:
                score = max(score, risk)
                reasons.append(f"Privilege escalation: {pattern}")

        for pattern, risk in self.NETWORK_RISK_COMMANDS.items():
            if pattern in cmd_lower:
                score = max(score, risk)
                reasons.append(f"Network operation: {pattern}")

        pipe_count = cmd_lower.count("|")
        if pipe_count > 3:
            score += 15
            reasons.append(f"Complex pipe chain ({pipe_count} pipes)")

        if re.search(r">\s*/", cmd_lower) or re.search(r">>\s*/", cmd_lower):
            score += 25
            reasons.append("Redirect to system path")

        if re.search(r"\|\s*(?:ba)?sh\b", cmd_lower):
            score += 30
            reasons.append("Piped script execution")
            blocked = True

        if re.search(r":\(\)\s*\{.*\|\s*&\s*\}", cmd_lower):
            score = 100
            reasons.append("Fork bomb detected")
            blocked = True

        env_vars = re.findall(r"(?:export\s+|ENV\s+)(\w+)", cmd_lower)
        sensitive_vars = [v for v in env_vars if any(s in v.lower() for s in ["key", "secret", "password", "token", "auth"])]
        if sensitive_vars:
            score += 20
            reasons.append(f"Sensitive env vars: {', '.join(sensitive_vars)}")

        if "rm -rf /" in cmd_lower or "rm -rf /*" in cmd_lower:
            score = 100
            blocked = True
            reasons.append("Attempted root filesystem deletion")

        score = min(100, max(0, score))
        level = self._score_to_level(score)

        return CommandRiskAssessment(
            command=command,
            score=score,
            level=level,
            reasons=reasons,
            blocked=blocked,
            requires_approval=score >= 60,
            sandbox_recommended=score >= 40,
            destructive_ops=destructive_ops,
        )

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
