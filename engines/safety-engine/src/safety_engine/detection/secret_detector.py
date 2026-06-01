"""Secret Detector — Detect secrets, API keys, and credentials in code/output"""
import re
from dataclasses import dataclass


@dataclass
class SecretMatch:
    pattern_name: str
    matched_text: str
    line_number: int
    confidence: float
    redacted: str


class SecretDetector:
    """Detect secrets and sensitive data in text."""

    PATTERNS = {
        "aws_access_key": {
            "regex": r"AKIA[0-9A-Z]{16}",
            "confidence": 0.95,
        },
        "aws_secret_key": {
            "regex": r"(?:aws_secret_access_key|secret_key)[=:]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
            "confidence": 0.90,
        },
        "github_token": {
            "regex": r"ghp_[A-Za-z0-9]{36}",
            "confidence": 0.95,
        },
        "github_oauth": {
            "regex": r"gho_[A-Za-z0-9]{36}",
            "confidence": 0.95,
        },
        "gitlab_token": {
            "regex": r"glpat-[A-Za-z0-9\-_]{20,}",
            "confidence": 0.95,
        },
        "slack_token": {
            "regex": r"xox[baprs]-[0-9]{10,}-[A-Za-z0-9\-]{10,}",
            "confidence": 0.95,
        },
        "slack_webhook": {
            "regex": r"https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+",
            "confidence": 0.90,
        },
        "stripe_key": {
            "regex": r"(?:sk|pk)_(?:live|test)_[0-9a-zA-Z]{24,}",
            "confidence": 0.95,
        },
        "google_api_key": {
            "regex": r"AIza[0-9A-Za-z\-_]{35}",
            "confidence": 0.90,
        },
        "heroku_api_key": {
            "regex": r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            "confidence": 0.3,  # Low confidence, many false positives
        },
        "private_key_header": {
            "regex": r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----",
            "confidence": 0.98,
        },
        "password_in_url": {
            "regex": r"://[^:]+:([^@]{8,})@",
            "confidence": 0.85,
        },
        "jwt_token": {
            "regex": r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+",
            "confidence": 0.90,
        },
        "generic_api_key": {
            "regex": r"(?:api[_-]?key|apikey|api_secret)[=:]\s*['\"]([A-Za-z0-9\-_]{20,})['\"]",
            "confidence": 0.70,
        },
        "generic_secret": {
            "regex": r"(?:secret|password|passwd|pwd)[=:]\s*['\"]([^'\"]{8,})['\"]",
            "confidence": 0.75,
        },
    }

    def scan_text(self, text: str) -> list[SecretMatch]:
        matches = []
        lines = text.split("\n")
        for line_num, line in enumerate(lines, 1):
            for name, config in self.PATTERNS.items():
                for m in re.finditer(config["regex"], line):
                    matched = m.group(0)
                    redacted = self._redact(matched)
                    matches.append(SecretMatch(
                        pattern_name=name,
                        matched_text=matched,
                        line_number=line_num,
                        confidence=config["confidence"],
                        redacted=redacted,
                    ))
        return matches

    def scan_file(self, path: str) -> list[SecretMatch]:
        try:
            with open(path, "r", errors="ignore") as f:
                return self.scan_text(f.read())
        except Exception:
            return []

    def has_secrets(self, text: str, threshold: float = 0.7) -> bool:
        matches = self.scan_text(text)
        return any(m.confidence >= threshold for m in matches)

    def redact_text(self, text: str) -> str:
        for name, config in self.PATTERNS.items():
            text = re.sub(config["regex"], f"[REDACTED:{name}]", text)
        return text

    def _redact(self, text: str) -> str:
        if len(text) <= 8:
            return "*" * len(text)
        return text[:4] + "*" * (len(text) - 8) + text[-4:]
