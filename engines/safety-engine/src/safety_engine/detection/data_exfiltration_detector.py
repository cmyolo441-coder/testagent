"""Data Exfiltration Detector — Detect attempts to exfiltrate data"""
import re
from dataclasses import dataclass
from safety_engine.risk.risk_model import RiskLevel


@dataclass
class ExfiltrationMatch:
    technique: str
    command: str
    confidence: float
    severity: str
    details: str

    def to_dict(self) -> dict:
        return {
            "technique": self.technique,
            "command": self.command,
            "confidence": self.confidence,
            "severity": self.severity,
            "details": self.details,
        }


@dataclass
class ExfiltrationDetectionResult:
    is_exfiltration: bool
    risk_level: RiskLevel
    score: int
    matches: list[ExfiltrationMatch]
    techniques: list[str]

    def to_dict(self) -> dict:
        return {
            "is_exfiltration": self.is_exfiltration,
            "risk_level": self.risk_level.name,
            "score": self.score,
            "techniques": self.techniques,
            "matches": [m.to_dict() for m in self.matches],
        }


class DataExfiltrationDetector:
    """Detect data exfiltration attempts in commands and operations."""

    EXFIL_TECHNIQUES = {
        "http_upload": {
            "patterns": [
                r"curl\s+.*(?:-X\s*POST|-d\s|@|--data-binary|-T\s)",
                r"wget\s+.*--post-file",
                r"python.*requests\.(?:post|put)",
                r"python.*urllib",
                r"fetch\s*\(",
                r"XMLHttpRequest",
            ],
            "confidence": 0.80,
            "severity": "high",
        },
        "dns_exfil": {
            "patterns": [
                r"dig\s+.*TXT",
                r"nslookup\s+.*TXT",
                r"host\s+.*TXT",
                r"dns2tcp",
                r"iodine",
            ],
            "confidence": 0.75,
            "severity": "high",
        },
        "ssh_tunnel": {
            "patterns": [
                r"ssh\s+.*-[LRD]\s",
                r"ssh\s+.*-N\s+-L",
                r"ssh\s+.*-N\s+-R",
                r"scp\s+.*@.*:",
                r"rsync\s+.*@.*:",
            ],
            "confidence": 0.70,
            "severity": "high",
        },
        "netcat_exfil": {
            "patterns": [
                r"nc\s+.*-w\s.*<",
                r"ncat\s+.*<",
                r"netcat\s+.*<",
                r"nc\s+.*-e\s",
                r"nc\s+.*-c\s",
            ],
            "confidence": 0.85,
            "severity": "critical",
        },
        "file_archive": {
            "patterns": [
                r"tar\s+.*czf.*\s*/",
                r"zip\s+.*-r\s",
                r"7z\s+a\s",
                r"gzip\s+.*>",
                r"bzip2\s+.*>",
            ],
            "confidence": 0.50,
            "severity": "medium",
        },
        "encoded_data": {
            "patterns": [
                r"base64\s+(?:--encode|-e|[-]w\s*0)",
                r"base64\s.*\|\s*(?:curl|wget|nc)",
                r"xxd\s+.*\|\s*(?:curl|wget|nc)",
                r"openssl\s+enc\s+.*\|\s*(?:curl|wget)",
            ],
            "confidence": 0.75,
            "severity": "high",
        },
        "reverse_shell": {
            "patterns": [
                r"bash\s+-i\s+>&\s*/dev/tcp",
                r"/dev/tcp/.*/\d+",
                r"python.*socket.*connect",
                r"python.*subprocess.*shell=True.*socket",
                r"nc\s+.*-e\s+/bin/(?:ba)?sh",
                r"mkfifo\s+.*\snc",
            ],
            "confidence": 0.95,
            "severity": "critical",
        },
        "credential_access": {
            "patterns": [
                r"cat\s+.*(?:\.ssh|\.gnupg|\.aws|\.config).*credentials",
                r"cat\s+/etc/shadow",
                r"cat\s+/etc/passwd.*\|",
                r"(?:grep|find).*\.(?:key|pem|p12|pfx)",
                r"read\s+.*token\s+<\s*",
            ],
            "confidence": 0.80,
            "severity": "critical",
        },
        "memory_access": {
            "patterns": [
                r"/proc/self/mem",
                r"/proc/\d+/mem",
                r"dd\s+if=/dev/mem",
                r"dd\s+if=/dev/kmem",
                r"gdb\s+.*-p\s+\d+",
                r"strace\s+-e\s+read",
            ],
            "confidence": 0.85,
            "severity": "critical",
        },
    }

    DANGEROUS_PATHS = [
        r"/etc/(?:shadow|passwd|sudoers)",
        r"/\.ssh/(?:id_|authorized_keys|known_hosts|config)",
        r"/\.aws/(?:credentials|config)",
        r"/\.gnupg/",
        r"/\.kube/config",
        r"/\.docker/config\.json",
        r"/var/log/(?:auth|syslog|secure)",
        r"/proc/\d+/",
    ]

    def detect(self, operation: str) -> ExfiltrationDetectionResult:
        matches: list[ExfiltrationMatch] = []
        techniques: list[str] = []
        max_score = 0

        op_lower = operation.lower().strip()

        for technique, config in self.EXFIL_TECHNIQUES.items():
            for pattern in config["patterns"]:
                if re.search(pattern, op_lower):
                    match = ExfiltrationMatch(
                        technique=technique,
                        command=operation,
                        confidence=config["confidence"],
                        severity=config["severity"],
                        details=f"Matched pattern: {pattern}",
                    )
                    matches.append(match)
                    if technique not in techniques:
                        techniques.append(technique)
                    score = int(config["confidence"] * 100)
                    max_score = max(max_score, score)
                    break

        for path_pattern in self.DANGEROUS_PATHS:
            if re.search(path_pattern, op_lower):
                max_score = max(max_score, 75)
                if "credential_access" not in techniques:
                    techniques.append("credential_access")

        score = min(100, max(0, max_score))
        risk_level = self._score_to_level(score)

        return ExfiltrationDetectionResult(
            is_exfiltration=score >= 50,
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
