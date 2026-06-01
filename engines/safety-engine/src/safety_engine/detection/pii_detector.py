"""PII Detector — Detect personally identifiable information in text"""
import re
from dataclasses import dataclass, field


@dataclass
class PIIMatch:
    pii_type: str
    matched_text: str
    redacted: str
    confidence: float
    line_number: int
    start_pos: int
    end_pos: int

    def to_dict(self) -> dict:
        return {
            "pii_type": self.pii_type,
            "matched_text": self.redacted,
            "confidence": self.confidence,
            "line_number": self.line_number,
        }


@dataclass
class PIIDetectionResult:
    found: bool
    matches: list[PIIMatch] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)
    total_count: int = 0

    def to_dict(self) -> dict:
        return {
            "found": self.found,
            "total_count": self.total_count,
            "summary": self.summary,
            "matches": [m.to_dict() for m in self.matches],
        }


class PIIDetector:
    """Detect personally identifiable information in text."""

    PATTERNS = {
        "email": {
            "regex": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "confidence": 0.95,
            "severity": "high",
        },
        "phone_us": {
            "regex": r"(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
            "confidence": 0.85,
            "severity": "medium",
        },
        "phone_intl": {
            "regex": r"\+(?:[0-9][\- ]?){6,14}[0-9]",
            "confidence": 0.80,
            "severity": "medium",
        },
        "ssn": {
            "regex": r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b",
            "confidence": 0.90,
            "severity": "critical",
        },
        "credit_card_visa": {
            "regex": r"\b4\d{3}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
            "confidence": 0.90,
            "severity": "critical",
        },
        "credit_card_mastercard": {
            "regex": r"\b5[1-5]\d{2}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
            "confidence": 0.90,
            "severity": "critical",
        },
        "credit_card_amex": {
            "regex": r"\b3[47]\d{2}[- ]?\d{6}[- ]?\d{5}\b",
            "confidence": 0.90,
            "severity": "critical",
        },
        "passport_us": {
            "regex": r"\b[A-Z]\d{8}\b",
            "confidence": 0.75,
            "severity": "high",
        },
        "drivers_license": {
            "regex": r"\b[A-Z]\d{7,14}\b",
            "confidence": 0.60,
            "severity": "medium",
        },
        "date_of_birth": {
            "regex": r"\b(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])\b",
            "confidence": 0.70,
            "severity": "high",
        },
        "ip_address_v4": {
            "regex": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "confidence": 0.80,
            "severity": "medium",
        },
        "mac_address": {
            "regex": r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b",
            "confidence": 0.85,
            "severity": "medium",
        },
        "iban": {
            "regex": r"\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b",
            "confidence": 0.70,
            "severity": "high",
        },
        "aws_access_key": {
            "regex": r"\bAKIA[0-9A-Z]{16}\b",
            "confidence": 0.95,
            "severity": "critical",
        },
        "github_token": {
            "regex": r"\bghp_[A-Za-z0-9]{36}\b",
            "confidence": 0.95,
            "severity": "critical",
        },
        "slack_token": {
            "regex": r"\bxox[baprs]-[0-9]{10,}-[A-Za-z0-9\-]{10,}\b",
            "confidence": 0.95,
            "severity": "critical",
        },
        "private_key": {
            "regex": r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----",
            "confidence": 0.98,
            "severity": "critical",
        },
        "password_in_text": {
            "regex": r"(?:password|passwd|pwd)\s*[=:]\s*['\"]([^'\"]{8,})['\"]",
            "confidence": 0.85,
            "severity": "critical",
        },
        "api_key_assignment": {
            "regex": r"(?:api[_-]?key|apikey)\s*[=:]\s*['\"]([A-Za-z0-9\-_]{20,})['\"]",
            "confidence": 0.80,
            "severity": "high",
        },
    }

    REDACT_MAP = {
        "email": lambda m: m[:2] + "***@" + m.split("@")[1] if "@" in m else "***",
        "phone_us": lambda m: "***-***-" + m[-4:] if len(m) >= 4 else "***",
        "ssn": lambda m: "***-**-" + m[-4:] if len(m) >= 4 else "***",
        "credit_card_visa": lambda m: "****-****-****-" + m[-4:] if len(m) >= 4 else "***",
        "credit_card_mastercard": lambda m: "****-****-****-" + m[-4:] if len(m) >= 4 else "***",
        "credit_card_amex": lambda m: "****-******-" + m[-5:] if len(m) >= 5 else "***",
        "aws_access_key": lambda m: m[:4] + "****" + m[-4:] if len(m) >= 8 else "***",
        "github_token": lambda m: "ghp_****" + m[-4:] if len(m) >= 8 else "***",
        "slack_token": lambda m: m[:10] + "****" if len(m) >= 10 else "***",
        "private_key": lambda m: "[REDACTED_PRIVATE_KEY]",
    }

    def detect(self, text: str) -> PIIDetectionResult:
        matches: list[PIIMatch] = []
        lines = text.split("\n")

        for line_num, line in enumerate(lines, 1):
            for pii_name, config in self.PATTERNS.items():
                for m in re.finditer(config["regex"], line):
                    matched = m.group(0)
                    redact_fn = self.REDACT_MAP.get(pii_name, lambda x: "***REDACTED***")
                    matches.append(PIIMatch(
                        pii_type=pii_name,
                        matched_text=matched,
                        redacted=redact_fn(matched),
                        confidence=config["confidence"],
                        line_number=line_num,
                        start_pos=m.start(),
                        end_pos=m.end(),
                    ))

        summary: dict[str, int] = {}
        for match in matches:
            summary[match.pii_type] = summary.get(match.pii_type, 0) + 1

        return PIIDetectionResult(
            found=len(matches) > 0,
            matches=matches,
            summary=summary,
            total_count=len(matches),
        )

    def redact(self, text: str) -> str:
        for pii_name, config in self.PATTERNS.items():
            redact_fn = self.REDACT_MAP.get(pii_name, lambda x: "***REDACTED***")
            text = re.sub(config["regex"], redact_fn, text)
        return text

    def has_pii(self, text: str, min_confidence: float = 0.7) -> bool:
        for config in self.PATTERNS.values():
            if config["confidence"] < min_confidence:
                continue
            if re.search(config["regex"], text):
                return True
        return False
