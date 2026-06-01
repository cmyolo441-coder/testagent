"""Package Risk — Assess risk of package installation and dependency operations"""
import re
from dataclasses import dataclass
from safety_engine.risk.risk_model import RiskLevel


@dataclass
class PackageRiskAssessment:
    operation: str
    package_name: str
    score: int
    level: RiskLevel
    reasons: list[str]
    blocked: bool
    requires_approval: bool
    audit_recommended: bool

    def to_dict(self) -> dict:
        return {
            "operation": self.operation,
            "package_name": self.package_name,
            "score": self.score,
            "level": self.level.name,
            "reasons": self.reasons,
            "blocked": self.blocked,
            "requires_approval": self.requires_approval,
            "audit_recommended": self.audit_recommended,
        }


class PackageRisk:
    """Assess risk of package manager operations."""

    KNOWN_MALICIOUS_PACKAGES = {
        "event-stream", "flatmap-stream", "crossenv", "mongose",
        "nodemailer-js", "getcookies", "npm-script-runner",
        "colour-codes", "baresip", "discord-loo", "getdiscord",
    }

    TYPOSQUAT_CANDIDATES = {
        "expresss", "lodahs", "requst", "axois", "reactt",
        "lodashs", "momentt", "webpackk", "browerser",
    }

    HIGH_RISK_PACKAGES = {
        "eval", "child_process", "shelljs", "sudo-prompt",
        "node-pty", "pty.js", "electron", "nwjs",
    }

    OPERATIONS_RISK = {
        "install": 30, "uninstall": 25, "update": 20,
        "upgrade": 20, "link": 45, "publish": 60,
        "pack": 25, "audit": 10, "outdated": 5,
        "dedupe": 35, "rebuild": 30,
    }

    MANAGERS = {
        "npm": {"install": "npm install", "uninstall": "npm uninstall"},
        "pip": {"install": "pip install", "uninstall": "pip uninstall"},
        "apt": {"install": "apt install", "uninstall": "apt remove"},
        "yum": {"install": "yum install", "uninstall": "yum remove"},
        "dnf": {"install": "dnf install", "uninstall": "dnf remove"},
        "brew": {"install": "brew install", "uninstall": "brew uninstall"},
        "cargo": {"install": "cargo install", "uninstall": "cargo uninstall"},
        "gem": {"install": "gem install", "uninstall": "gem uninstall"},
        "nuget": {"install": "nuget install", "uninstall": "nuget uninstall"},
    }

    def assess_package_risk(self, operation: str, package_name: str = "") -> PackageRiskAssessment:
        score = 0
        reasons: list[str] = []
        audit_recommended = False

        op_lower = operation.lower().strip()
        pkg = package_name.strip()

        for op_key, risk in self.OPERATIONS_RISK.items():
            if op_key in op_lower:
                score = max(score, risk)
                reasons.append(f"Operation: {op_key}")

        if pkg:
            pkg_lower = pkg.lower()

            if pkg_lower in self.KNOWN_MALICIOUS_PACKAGES:
                score = 95
                reasons.append(f"Known malicious package: {pkg}")
                audit_recommended = True

            if pkg_lower in self.TYPOSQUAT_CANDIDATES:
                score = max(score, 80)
                reasons.append(f"Possible typosquat: {pkg}")
                audit_recommended = True

            if pkg_lower in self.HIGH_RISK_PACKAGES:
                score = max(score, 55)
                reasons.append(f"High-risk package: {pkg}")

            if pkg_lower.startswith("@") and "/" in pkg_lower:
                score = max(score, 35)
                reasons.append(f"Scoped package: {pkg}")

            if re.search(r"^(?:https?://|git\+|github:|gitlab:)", pkg_lower):
                score = max(score, 50)
                reasons.append("Git/URL source package")

            if len(pkg_lower) < 4 and not pkg_lower.startswith(("@", "go-", "lib")):
                score = max(score, 30)
                reasons.append(f"Very short package name (possible squat): {pkg}")

            if re.search(r"[^a-z0-9\-_.@/]", pkg_lower):
                score = max(score, 25)
                reasons.append("Unusual characters in package name")

            if "latest" in pkg_lower or "*" in pkg:
                score = max(score, 40)
                reasons.append("Wildcard/latest version pin")

        if "force" in op_lower or "--force" in op_lower:
            score = max(score, 45)
            reasons.append("Force flag used")

        if "global" in op_lower:
            score = max(score, 50)
            reasons.append("Global installation")

        if "pre" in op_lower or "rc" in op_lower or "beta" in op_lower or "alpha" in op_lower:
            score = max(score, 35)
            reasons.append("Pre-release version")
            audit_recommended = True

        if "--no-save" in op_lower or "--save-dev" not in op_lower:
            score = max(score, 25)
            reasons.append("Dependency not recorded in manifest")

        score = min(100, max(0, score))
        level = self._score_to_level(score)

        return PackageRiskAssessment(
            operation=operation,
            package_name=package_name,
            score=score,
            level=level,
            reasons=reasons,
            blocked=score >= 90,
            requires_approval=score >= 50,
            audit_recommended=audit_recommended,
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
