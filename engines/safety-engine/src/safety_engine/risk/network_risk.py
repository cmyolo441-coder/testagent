"""Network Risk — Assess risk of network operations"""
import re
from dataclasses import dataclass
from safety_engine.risk.risk_model import RiskLevel


@dataclass
class NetworkRiskAssessment:
    operation: str
    target: str
    score: int
    level: RiskLevel
    reasons: list[str]
    blocked: bool
    requires_approval: bool
    data_loss_risk: bool

    def to_dict(self) -> dict:
        return {
            "operation": self.operation,
            "target": self.target,
            "score": self.score,
            "level": self.level.name,
            "reasons": self.reasons,
            "blocked": self.blocked,
            "requires_approval": self.requires_approval,
            "data_loss_risk": self.data_loss_risk,
        }


class NetworkRisk:
    """Assess risk of network operations."""

    HIGH_RISK_PORTS = {22: 40, 23: 50, 25: 35, 53: 25, 110: 30, 143: 30,
                       445: 60, 1433: 50, 1521: 50, 3306: 50, 3389: 60,
                       5432: 50, 5900: 55, 6379: 45, 27017: 45}

    PROTOCOL_RISK = {
        "http": 20, "https": 10, "ftp": 40, "ftps": 20,
        "ssh": 30, "telnet": 60, "smtp": 35, "smtps": 25,
        "pop3": 30, "imap": 30, "dns": 25,
        "tcp": 30, "udp": 35, "icmp": 20,
        "sftp": 20, "scp": 25, "rsync": 15,
        "websocket": 30, "grpc": 25,
    }

    DATA_EXFIL_PATTERNS = [
        (r"curl.*-d\s", "POST data via curl"),
        (r"wget.*--post-file", "File upload via wget"),
        (r"nc\s.*-w", "Data transfer via netcat"),
        (r"rsync.*@", "Remote sync"),
        (r"scp\s.*@", "Secure copy to remote"),
        (r"ssh\s.*cat\s*>", "SSH tunnel exfil"),
        (r"python.*socket.*connect", "Raw socket connection"),
        (r"requests\.post", "Python POST request"),
        (r"fetch\(", "JavaScript fetch"),
    ]

    LOCALHOST_PATTERNS = [
        r"127\.0\.0\.1", r"localhost", r"0\.0\.0\.0",
        r"::1", r"\[::1\]",
    ]

    INTERNET_RANGES = [
        r"^(\d{1,3}\.){3}\d{1,3}$",
    ]

    def assess_network_risk(self, operation: str, target: str = "") -> NetworkRiskAssessment:
        score = 0
        reasons: list[str] = []
        data_loss_risk = False

        op_lower = operation.lower().strip()
        target_lower = target.lower().strip()

        for protocol, risk in self.PROTOCOL_RISK.items():
            if protocol in op_lower:
                score = max(score, risk)
                reasons.append(f"Protocol: {protocol}")

        port_match = re.search(r":(\d+)", target)
        if port_match:
            port = int(port_match.group(1))
            if port in self.HIGH_RISK_PORTS:
                score = max(score, self.HIGH_RISK_PORTS[port])
                reasons.append(f"High-risk port: {port}")

        for pattern, desc in self.DATA_EXFIL_PATTERNS:
            if re.search(pattern, op_lower):
                score = max(score, 55)
                reasons.append(f"Data exfiltration pattern: {desc}")
                data_loss_risk = True

        if any(re.search(p, target_lower) for p in self.LOCALHOST_PATTERNS):
            score = max(0, score - 15)
            reasons.append("Localhost target (reduced risk)")

        if target_lower.startswith("http"):
            if "download" in op_lower or "get" in op_lower:
                score = max(score, 25)
                reasons.append("Download from web")

        if "upload" in op_lower or "put" in op_lower or "post" in op_lower:
            score = max(score, 35)
            reasons.append("Upload/POST operation")

        if "proxy" in op_lower or "tunnel" in op_lower:
            score = max(score, 40)
            reasons.append("Proxy/tunnel usage")

        if "dns" in op_lower and ("query" in op_lower or "resolve" in op_lower):
            score = max(score, 15)
            reasons.append("DNS resolution")

        if re.search(r"(?:0\.0\.0\.0|255\.255\.255\.255|broadcast)", target_lower):
            score = max(score, 45)
            reasons.append("Broadcast/all-interfaces binding")

        if "firewall" in op_lower or "iptables" in op_lower:
            score = max(score, 50)
            reasons.append("Firewall modification")

        score = min(100, max(0, score))
        level = self._score_to_level(score)

        return NetworkRiskAssessment(
            operation=operation,
            target=target,
            score=score,
            level=level,
            reasons=reasons,
            blocked=score >= 90,
            requires_approval=score >= 55,
            data_loss_risk=data_loss_risk,
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
