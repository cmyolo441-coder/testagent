"""Supply Chain Detector — Detect supply chain attack patterns"""
import re
from dataclasses import dataclass
from safety_engine.risk.risk_model import RiskLevel


@dataclass
class SupplyChainMatch:
    threat_type: str
    package: str
    confidence: float
    severity: str
    details: str

    def to_dict(self) -> dict:
        return {
            "threat_type": self.threat_type,
            "package": self.package,
            "confidence": self.confidence,
            "severity": self.severity,
            "details": self.details,
        }


@dataclass
class SupplyChainDetectionResult:
    is_suspicious: bool
    risk_level: RiskLevel
    score: int
    matches: list[SupplyChainMatch]
    threats: list[str]

    def to_dict(self) -> dict:
        return {
            "is_suspicious": self.is_suspicious,
            "risk_level": self.risk_level.name,
            "score": self.score,
            "threats": self.threats,
            "matches": [m.to_dict() for m in self.matches],
        }


class SupplyChainDetector:
    """Detect supply chain attack patterns in package operations."""

    KNOWN_MALICIOUS_PACKAGES = {
        "npm": {
            "event-stream": {"version": "0.9.10", "threat": "cryptomining backdoor"},
            "flatmap-stream": {"version": "0.1.1", "threat": "dependency confusion"},
            "crossenv": {"version": None, "threat": "typosquat of cross-env"},
            "mongose": {"version": None, "threat": "typosquat of mongoose"},
            "nodemailer-js": {"version": None, "threat": "typosquat of nodemailer"},
            "getcookies": {"version": None, "threat": "data exfiltration"},
            "npm-script-runner": {"version": None, "threat": "typosquat of cross-spawn"},
            "baresip": {"version": None, "threat": "typosquat of bare"},
            "discord-loo": {"version": None, "threat": "typosquat of discord.js"},
        },
        "pypi": {
            "python-dateutil-shim": {"version": None, "threat": "dependency confusion"},
            "jeIlyfish": {"version": None, "threat": "typosquat of jellyfish"},
            "jeLLyfish": {"version": None, "threat": "typosquat of jellyfish"},
            "colour-codes": {"version": None, "threat": "malicious package"},
            "crypto-uuid": {"version": None, "threat": "typosquat of uuid"},
        },
    }

    TYPOSQUAT_INDICATORS = [
        (r"^[a-z]+-[a-z]+$", "hyphenated-variant"),
        (r"[0-9]$", "trailing-number"),
        (r"(.)(\1)", "doubled-character"),
        (r"^(?:get|set|go|my|the)-", "common-prefix"),
    ]

    SUSPICIOUS_PATTERNS = {
        "postinstall_script": {
            "regex": r"(?:postinstall|preinstall|install)\s*(?:&&|\|\||;)\s*(?:curl|wget|nc|python|node)",
            "confidence": 0.90,
            "severity": "critical",
        },
        "obfuscated_code": {
            "regex": r"(?:eval|Function)\s*\(\s*['\"].*(?:\\x|\\u|atob|btoa)",
            "confidence": 0.85,
            "severity": "high",
        },
        "network_in_install": {
            "regex": r"(?:curl|wget|fetch|http\.request)\s*\(.*install",
            "confidence": 0.80,
            "severity": "high",
        },
        "dynamic_require": {
            "regex": r"require\s*\(\s*(?:globalThis|process\.env|Buffer)",
            "confidence": 0.75,
            "severity": "high",
        },
        "git_dependency": {
            "regex": r"(?:github|gitlab|bitbucket)\.com.*#\s*(?:HEAD|main|master)",
            "confidence": 0.65,
            "severity": "medium",
        },
        "url_dependency": {
            "regex": r"(?:https?://|git\+https?://).*\.(?:tar\.gz|zip|tgz)",
            "confidence": 0.80,
            "severity": "high",
        },
        "private_registry": {
            "regex": r"(?:registry|--registry)\s*[=:]\s*(?:https?://(?!registry\.npmjs|pypi\.org))",
            "confidence": 0.70,
            "severity": "medium",
        },
    }

    def detect(self, package_info: str) -> SupplyChainDetectionResult:
        matches: list[SupplyChainMatch] = []
        threats: list[str] = []
        max_score = 0

        pkg_lower = package_info.lower().strip()

        for ecosystem, packages in self.KNOWN_MALICIOUS_PACKAGES.items():
            for pkg_name, info in packages.items():
                if pkg_name.lower() in pkg_lower:
                    match = SupplyChainMatch(
                        threat_type="known_malicious",
                        package=pkg_name,
                        confidence=0.95,
                        severity="critical",
                        details=f"{info['threat']} (ecosystem: {ecosystem})",
                    )
                    matches.append(match)
                    threats.append(f"Known malicious: {pkg_name}")
                    max_score = max(max_score, 95)

        for pkg_name in self._extract_package_names(package_info):
            pkg_lower_name = pkg_name.lower()
            for indicator, threat_type in self.TYPOSQUAT_INDICATORS:
                if re.search(indicator, pkg_lower_name):
                    match = SupplyChainMatch(
                        threat_type="typosquat",
                        package=pkg_name,
                        confidence=0.65,
                        severity="high",
                        details=f"Typosquat indicator: {threat_type}",
                    )
                    matches.append(match)
                    threats.append(f"Possible typosquat: {pkg_name}")
                    max_score = max(max_score, 65)

        for threat_type, config in self.SUSPICIOUS_PATTERNS.items():
            if re.search(config["regex"], pkg_lower):
                match = SupplyChainMatch(
                    threat_type=threat_type,
                    package=package_info[:100],
                    confidence=config["confidence"],
                    severity=config["severity"],
                    details=f"Suspicious pattern: {threat_type}",
                )
                matches.append(match)
                threats.append(f"Suspicious: {threat_type}")
                score = int(config["confidence"] * 100)
                max_score = max(max_score, score)

        if not pkg_lower.startswith(("npm", "pip", "apt", "yarn", "pnpm", "cargo", "gem", "go")):
            if "github.com" in pkg_lower or "gitlab.com" in pkg_lower:
                match = SupplyChainMatch(
                    threat_type="git_source",
                    package=package_info[:100],
                    confidence=0.50,
                    severity="medium",
                    details="Package from git source",
                )
                matches.append(match)
                max_score = max(max_score, 50)

        score = min(100, max(0, max_score))
        risk_level = self._score_to_level(score)

        return SupplyChainDetectionResult(
            is_suspicious=score >= 50,
            risk_level=risk_level,
            score=score,
            matches=matches,
            threats=threats,
        )

    def _extract_package_names(self, text: str) -> list[str]:
        names = re.findall(r"(?:npm\s+install\s+|pip\s+install\s+|yarn\s+add\s+)([\w@/.-]+)", text)
        return names

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
