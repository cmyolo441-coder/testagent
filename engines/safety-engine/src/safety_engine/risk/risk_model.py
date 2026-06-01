"""Risk Model — Real risk scoring for commands and file operations"""
import re
import os
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    SAFE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class RiskAssessment:
    score: int  # 0-100
    level: RiskLevel
    reasons: list[str]
    requires_approval: bool
    dry_run_recommended: bool

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "level": self.level.name,
            "reasons": self.reasons,
            "requires_approval": self.requires_approval,
            "dry_run_recommended": self.dry_run_recommended,
        }


class RiskAssessor:
    """Assess risk of commands and file operations."""

    DANGEROUS_COMMANDS = {
        "rm": 40, "rm -rf": 80, "rm -r": 70, "rmdir": 30,
        "mkfs": 100, "dd": 90, "format": 100,
        "chmod": 30, "chown": 40, "chgrp": 30,
        "sudo": 60, "su": 50, "passwd": 70,
        "kill": 40, "kill -9": 60, "pkill": 40,
        "shutdown": 50, "reboot": 50, "halt": 50,
        "mount": 40, "umount": 40,
        "fdisk": 80, "parted": 80,
        "iptables": 60, "nft": 60,
        "curl": 20, "wget": 20,
        "ssh": 30, "scp": 30, "rsync": 20,
        "docker": 30, "docker rm": 50, "docker rmi": 40,
        "kubectl": 30, "kubectl delete": 60,
        "git push --force": 60, "git reset --hard": 50,
        "npm publish": 50, "pip upload": 50,
        "DROP TABLE": 100, "DELETE FROM": 80, "TRUNCATE": 90,
    }

    SAFE_PATTERNS = [
        r"^ls\b", r"^pwd\b", r"^echo\b", r"^cat\b", r"^head\b", r"^tail\b",
        r"^grep\b", r"^find\b", r"^wc\b", r"^sort\b", r"^uniq\b",
        r"^python\b", r"^pip install\b", r"^npm install\b",
        r"^git status\b", r"^git log\b", r"^git diff\b",
        r"^mkdir\b", r"^touch\b", r"^cp\b",
    ]

    DESTRUCTIVE_PATHS = [
        "/etc", "/usr", "/bin", "/sbin", "/boot", "/root",
        "/var/log", "/proc", "/sys", "/dev",
    ]

    def assess_command(self, command: str) -> int:
        score = 0
        reasons = []
        cmd_lower = command.lower().strip()

        # Check dangerous commands
        for pattern, risk_score in self.DANGEROUS_COMMANDS.items():
            if pattern in cmd_lower:
                score = max(score, risk_score)
                reasons.append(f"Dangerous command pattern: {pattern}")

        # Check for pipe chains (more complex = more risky)
        pipes = cmd_lower.count("|")
        if pipes > 2:
            score += 10
            reasons.append(f"Complex pipe chain ({pipes} pipes)")

        # Check for output redirection to system paths
        if re.search(r">\s*/", cmd_lower) or re.search(r">>\s*/", cmd_lower):
            score += 30
            reasons.append("Writing to system path")

        # Check for environment variable manipulation
        if "export" in cmd_lower or "env " in cmd_lower:
            score += 10
            reasons.append("Environment variable manipulation")

        # Check for network operations
        if any(x in cmd_lower for x in ["curl", "wget", "nc", "netcat", "telnet"]):
            score += 15
            reasons.append("Network operation")

        # Check for recursive operations
        if "-r" in cmd_lower or "-rf" in cmd_lower or "--recursive" in cmd_lower:
            score += 15
            reasons.append("Recursive operation")

        # Safe patterns reduce risk
        for pattern in self.SAFE_PATTERNS:
            if re.match(pattern, cmd_lower):
                score = max(0, score - 20)
                break

        return min(100, max(0, score))

    def assess_file_write(self, path: str) -> int:
        score = 0
        reasons = []

        # Check destructive paths
        for dp in self.DESTRUCTIVE_PATHS:
            if path.startswith(dp):
                score = 90
                reasons.append(f"Writing to system path: {dp}")
                break

        # Check for hidden files
        if os.path.basename(path).startswith("."):
            score += 10
            reasons.append("Hidden file")

        # Check for config files
        if path.endswith((".json", ".yaml", ".yml", ".toml", ".ini", ".cfg")):
            score += 15
            reasons.append("Configuration file")

        # Check for executable files
        if path.endswith((".sh", ".bash", ".py", ".pl", ".rb")):
            score += 10
            reasons.append("Executable file")

        return min(100, max(0, score))

    def assess_file_delete(self, path: str) -> int:
        score = 50  # Base score for any deletion
        reasons = ["File deletion"]

        for dp in self.DESTRUCTIVE_PATHS:
            if path.startswith(dp):
                score = 95
                reasons.append(f"System path deletion: {dp}")

        if "*" in path or "?" in path:
            score += 20
            reasons.append("Wildcard deletion")

        return min(100, max(0, score))

    def full_assessment(self, action: str, target: str = "") -> RiskAssessment:
        if action == "command":
            score = self.assess_command(target)
        elif action == "file_write":
            score = self.assess_file_write(target)
        elif action == "file_delete":
            score = self.assess_file_delete(target)
        else:
            score = 50

        if score >= 80:
            level = RiskLevel.CRITICAL
        elif score >= 60:
            level = RiskLevel.HIGH
        elif score >= 40:
            level = RiskLevel.MEDIUM
        elif score >= 20:
            level = RiskLevel.LOW
        else:
            level = RiskLevel.SAFE

        return RiskAssessment(
            score=score,
            level=level,
            reasons=[],
            requires_approval=score >= 60,
            dry_run_recommended=score >= 40,
        )
