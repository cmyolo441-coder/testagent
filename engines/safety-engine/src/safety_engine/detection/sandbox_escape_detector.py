"""Sandbox Escape Detector — Detect sandbox/container escape attempts"""
import re
from dataclasses import dataclass
from safety_engine.risk.risk_model import RiskLevel


@dataclass
class EscapeMatch:
    technique: str
    pattern: str
    confidence: float
    severity: str
    details: str

    def to_dict(self) -> dict:
        return {
            "technique": self.technique,
            "confidence": self.confidence,
            "severity": self.severity,
            "details": self.details,
        }


@dataclass
class EscapeDetectionResult:
    is_escape_attempt: bool
    risk_level: RiskLevel
    score: int
    matches: list[EscapeMatch]
    techniques: list[str]

    def to_dict(self) -> dict:
        return {
            "is_escape_attempt": self.is_escape_attempt,
            "risk_level": self.risk_level.name,
            "score": self.score,
            "techniques": self.techniques,
            "matches": [m.to_dict() for m in self.matches],
        }


class SandboxEscapeDetector:
    """Detect sandbox and container escape attempts."""

    ESCAPE_TECHNIQUES = {
        "container_escape": {
            "patterns": [
                r"docker\s+run\s+.*--privileged",
                r"docker\s+run\s+.*--cap-add\s+SYS_ADMIN",
                r"docker\s+run\s+.*-v\s+/:/",
                r"docker\s+run\s+.*--pid=host",
                r"docker\s+run\s+.*--net=host",
                r"docker\s+exec\s+.*nsenter",
            ],
            "confidence": 0.90,
            "severity": "critical",
        },
        "namespace_escape": {
            "patterns": [
                r"nsenter\s+.*-t\s+1",
                r"nsenter\s+.*--target\s+1",
                r"unshare\s+.*--mount",
                r"unshare\s+.*--pid",
                r"unshare\s+.*--net",
            ],
            "confidence": 0.85,
            "severity": "critical",
        },
        "cgroup_escape": {
            "patterns": [
                r"mount\s+.*cgroup",
                r"mount\s+-t\s+cgroup",
                r"/sys/fs/cgroup",
                r"cgroup.*release_agent",
                r"cgroup.*notify_on_release",
            ],
            "confidence": 0.80,
            "severity": "high",
        },
        "proc_escape": {
            "patterns": [
                r"/proc/\d+/root",
                r"/proc/1/root",
                r"/proc/\d+/ns/",
                r"readlink\s+/proc/\d+/ns/",
                r"ls\s+/proc/\d+/root",
            ],
            "confidence": 0.75,
            "severity": "high",
        },
        "device_access": {
            "patterns": [
                r"/dev/sd[a-z]",
                r"/dev/nvme",
                r"/dev/vd[a-z]",
                r"mknod\s+.*\s+(b|c)\s+",
                r"/dev/mem",
                r"/dev/kmem",
            ],
            "confidence": 0.85,
            "severity": "critical",
        },
        "kernel_exploit": {
            "patterns": [
                r"insmod\s+.*\.ko",
                r"modprobe\s+",
                r"mount\s+.*-o\s+loop",
                r".pivot_root",
                r"chroot\s+/",
            ],
            "confidence": 0.90,
            "severity": "critical",
        },
        "network_escape": {
            "patterns": [
                r"ip\s+link\s+set\s+.*(?:up|down)",
                r"ip\s+route\s+add",
                r"iptables\s+-I\s+FORWARD",
                r"tc\s+qdisc\s+add",
                r"brctl\s+addif",
            ],
            "confidence": 0.70,
            "severity": "high",
        },
        "mount_escape": {
            "patterns": [
                r"mount\s+(?:--bind|-o\s+bind)",
                r"mount\s+.*proc",
                r"mount\s+.*sysfs",
                r"mount\s+.*devpts",
                r"umount\s+.*/proc",
            ],
            "confidence": 0.80,
            "severity": "high",
        },
        "syscall_abuse": {
            "patterns": [
                r"ptrace\s+",
                r"PTRACE_ATTACH",
                r"seccomp\s+--unotify",
                r"userfaultfd",
                r"io_uring",
            ],
            "confidence": 0.75,
            "severity": "high",
        },
    }

    PROTECTED_PATHS = [
        r"/proc/1/", r"/sys/fs/cgroup", r"/dev/",
        r"/etc/shadow", r"/etc/passwd",
    ]

    def detect(self, operation: str) -> EscapeDetectionResult:
        matches: list[EscapeMatch] = []
        techniques: list[str] = []
        max_score = 0

        op_lower = operation.lower().strip()

        for technique, config in self.ESCAPE_TECHNIQUES.items():
            for pattern in config["patterns"]:
                if re.search(pattern, op_lower):
                    match = EscapeMatch(
                        technique=technique,
                        pattern=pattern,
                        confidence=config["confidence"],
                        severity=config["severity"],
                        details=f"Escape technique: {technique}",
                    )
                    matches.append(match)
                    if technique not in techniques:
                        techniques.append(technique)
                    score = int(config["confidence"] * 100)
                    max_score = max(max_score, score)
                    break

        for path in self.PROTECTED_PATHS:
            if re.search(path, op_lower):
                max_score = max(max_score, 60)
                if "proc_access" not in techniques:
                    techniques.append("proc_access")

        score = min(100, max(0, max_score))
        risk_level = self._score_to_level(score)

        return EscapeDetectionResult(
            is_escape_attempt=score >= 50,
            risk_level=risk_level,
            score=score,
            matches=matches,
            techniques=techniques,
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
