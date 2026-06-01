"""Data Risk — Assess risk of data operations (read, write, transfer)"""
import re
from dataclasses import dataclass
from safety_engine.risk.risk_model import RiskLevel


@dataclass
class DataRiskAssessment:
    operation: str
    data_type: str
    score: int
    level: RiskLevel
    reasons: list[str]
    blocked: bool
    requires_approval: bool
    encryption_recommended: bool
    audit_recommended: bool

    def to_dict(self) -> dict:
        return {
            "operation": self.operation,
            "data_type": self.data_type,
            "score": self.score,
            "level": self.level.name,
            "reasons": self.reasons,
            "blocked": self.blocked,
            "requires_approval": self.requires_approval,
            "encryption_recommended": self.encryption_recommended,
            "audit_recommended": self.audit_recommended,
        }


class DataRisk:
    """Assess risk of data operations based on content sensitivity."""

    PII_PATTERNS = {
        "email": {
            "regex": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "risk": 40,
        },
        "phone_us": {
            "regex": r"(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
            "risk": 35,
        },
        "ssn": {
            "regex": r"\d{3}-\d{2}-\d{4}",
            "risk": 80,
        },
        "credit_card": {
            "regex": r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}",
            "risk": 75,
        },
        "ip_address": {
            "regex": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "risk": 25,
        },
        "passport": {
            "regex": r"\b[A-Z]{1,2}\d{6,9}\b",
            "risk": 70,
        },
        "drivers_license": {
            "regex": r"\b[A-Z]\d{7,14}\b",
            "risk": 65,
        },
        "date_of_birth": {
            "regex": r"\b(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])\b",
            "risk": 45,
        },
    }

    SENSITIVE_DATA_TYPES = {
        "password": 85, "secret": 90, "token": 85,
        "api_key": 85, "apikey": 85, "private_key": 95,
        "credential": 80, "auth": 75,
        "database_url": 60, "connection_string": 60,
    }

    TRANSFER_RISK = {
        "email": 50, "upload": 40, "download": 30,
        "backup": 25, "archive": 20, "sync": 30,
        "share": 45, "export": 35, "import": 35,
        "broadcast": 55, "webhook": 40,
    }

    OPERATION_RISK = {
        "read": 15, "write": 25, "delete": 50,
        "copy": 20, "move": 25, "transform": 20,
        "encrypt": 15, "decrypt": 20, "hash": 10,
        "aggregate": 15, "analyze": 15, "export": 30,
    }

    def assess_data_risk(self, operation: str, data: str = "",
                         data_type: str = "", metadata: dict = None) -> DataRiskAssessment:
        score = 0
        reasons: list[str] = []
        encryption_recommended = False
        audit_recommended = False

        op_lower = operation.lower().strip()
        dt = data_type.lower().strip()

        for op_key, risk in self.OPERATION_RISK.items():
            if op_key in op_lower:
                score = max(score, risk)
                reasons.append(f"Operation: {op_key}")

        for sensitive_type, risk in self.SENSITIVE_DATA_TYPES.items():
            if sensitive_type in op_lower or sensitive_type in dt:
                score = max(score, risk)
                reasons.append(f"Sensitive data type: {sensitive_type}")
                encryption_recommended = True

        if data:
            for pii_name, config in self.PII_PATTERNS.items():
                if re.search(config["regex"], data):
                    score = max(score, config["risk"])
                    reasons.append(f"PII detected: {pii_name}")
                    audit_recommended = True
                    encryption_recommended = True

        if metadata:
            if "encrypted" in metadata and not metadata.get("encrypted"):
                score += 10
                reasons.append("Unencrypted data")
                encryption_recommended = True

            if "classification" in metadata:
                classification = metadata["classification"].lower()
                if classification in ("confidential", "secret", "top_secret"):
                    score = max(score, 70)
                    reasons.append(f"Classified data: {classification}")
                    encryption_recommended = True
                    audit_recommended = True
                elif classification == "internal":
                    score = max(score, 40)
                    reasons.append("Internal data")

        for transfer, risk in self.TRANSFER_RISK.items():
            if transfer in op_lower:
                score = max(score, risk)
                reasons.append(f"Transfer type: {transfer}")

        if "external" in op_lower or "public" in op_lower:
            score = max(score, 60)
            reasons.append("External/public exposure")
            audit_recommended = True

        if "batch" in op_lower or "bulk" in op_lower:
            score = max(score, 40)
            reasons.append("Bulk data operation")
            audit_recommended = True

        if "log" in op_lower and any(p in op_lower for p in ["write", "append", "create"]):
            score = max(score, 30)
            reasons.append("Data written to logs")

        score = min(100, max(0, score))
        level = self._score_to_level(score)

        detected_type = data_type or self._detect_data_type(data)

        return DataRiskAssessment(
            operation=operation,
            data_type=detected_type,
            score=score,
            level=level,
            reasons=reasons,
            blocked=score >= 90,
            requires_approval=score >= 60,
            encryption_recommended=encryption_recommended,
            audit_recommended=audit_recommended,
        )

    def _detect_data_type(self, data: str) -> str:
        if not data:
            return "unknown"
        for pii_name, config in self.PII_PATTERNS.items():
            if re.search(config["regex"], data):
                return pii_name
        return "generic"

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
