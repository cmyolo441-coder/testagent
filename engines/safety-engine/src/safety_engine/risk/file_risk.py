"""File Risk — Assess risk of file operations"""
import os
from pathlib import Path
from dataclasses import dataclass
from safety_engine.risk.risk_model import RiskLevel


@dataclass
class FileRiskAssessment:
    operation: str
    path: str
    score: int
    level: RiskLevel
    reasons: list[str]
    blocked: bool
    requires_approval: bool
    backup_recommended: bool

    def to_dict(self) -> dict:
        return {
            "operation": self.operation,
            "path": self.path,
            "score": self.score,
            "level": self.level.name,
            "reasons": self.reasons,
            "blocked": self.blocked,
            "requires_approval": self.requires_approval,
            "backup_recommended": self.backup_recommended,
        }


class FileRisk:
    """Assess risk of file system operations."""

    PROTECTED_PATHS = {
        "/etc": 90, "/usr": 85, "/bin": 90, "/sbin": 90,
        "/boot": 85, "/root": 80, "/var/log": 70,
        "/proc": 95, "/sys": 95, "/dev": 90,
        "/lib": 80, "/lib64": 80, "/opt": 60, "/srv": 50,
    }

    SENSITIVE_EXTENSIONS = {
        ".key": 95, ".pem": 90, ".p12": 90, ".pfx": 90,
        ".env": 85, ".credentials": 90, ".secret": 95,
        ".ssh": 85, ".gnupg": 85,
    }

    CONFIG_EXTENSIONS = {
        ".json": 30, ".yaml": 30, ".yml": 30, ".toml": 30,
        ".ini": 35, ".cfg": 35, ".conf": 35, ".config": 35,
    }

    EXECUTABLE_EXTENSIONS = {
        ".sh": 40, ".bash": 40, ".py": 30, ".pl": 35,
        ".rb": 35, ".js": 25, ".ts": 25, ".bashrc": 45,
        ".zshrc": 45, ".profile": 45, ".bash_profile": 45,
    }

    WRITE_OPERATIONS = {"write", "create", "append", "overwrite", "truncate"}
    DELETE_OPERATIONS = {"delete", "remove", "unlink", "shred"}
    MODIFY_OPERATIONS = {"chmod", "chown", "chgrp", "rename", "move"}

    def assess_file_risk(self, operation: str, path: str) -> FileRiskAssessment:
        score = 0
        reasons: list[str] = []
        backup_recommended = False

        op_lower = operation.lower().strip()
        path_obj = Path(path)

        for protected, risk in self.PROTECTED_PATHS.items():
            if path.startswith(protected) or path_obj.resolve().is_relative_to(Path(protected)):
                score = max(score, risk)
                reasons.append(f"Protected system path: {protected}")
                backup_recommended = True
                break

        ext = path_obj.suffix.lower()
        if ext in self.SENSITIVE_EXTENSIONS:
            score = max(score, self.SENSITIVE_EXTENSIONS[ext])
            reasons.append(f"Sensitive file type: {ext}")
            backup_recommended = True

        if ext in self.CONFIG_EXTENSIONS:
            score = max(score, self.CONFIG_EXTENSIONS[ext])
            reasons.append(f"Configuration file: {ext}")
            backup_recommended = True

        if ext in self.EXECUTABLE_EXTENSIONS:
            score = max(score, self.EXECUTABLE_EXTENSIONS[ext])
            reasons.append(f"Executable file: {ext}")

        if any(op in op_lower for op in self.DELETE_OPERATIONS):
            score = max(score, 50)
            reasons.append("Delete operation")
            backup_recommended = True

            if "*" in path or "?" in path:
                score = max(score, 70)
                reasons.append("Wildcard deletion")

        if any(op in op_lower for op in self.WRITE_OPERATIONS):
            score = max(score, 20)
            reasons.append("Write operation")

            if path_obj.exists():
                score = max(score, 30)
                reasons.append("Overwriting existing file")
                backup_recommended = True

        if any(op in op_lower for op in self.MODIFY_OPERATIONS):
            score = max(score, 30)
            reasons.append(f"Modify operation: {op_lower}")

            if op_lower in ("chmod", "chown"):
                score = max(score, 40)
                reasons.append("Permission change")

        if path_obj.name.startswith(".") and op_lower in self.DELETE_OPERATIONS:
            score = max(score, 45)
            reasons.append("Hidden file deletion")

        if path_obj.is_symlink():
            score = max(score, 25)
            reasons.append("Symbolic link operation")

        if ".." in path:
            score = max(score, 35)
            reasons.append("Path traversal detected")

        if op_lower in self.DELETE_OPERATIONS and not path_obj.exists():
            reasons.append("Non-existent path")

        score = min(100, max(0, score))
        level = self._score_to_level(score)

        return FileRiskAssessment(
            operation=operation,
            path=path,
            score=score,
            level=level,
            reasons=reasons,
            blocked=score >= 95,
            requires_approval=score >= 60,
            backup_recommended=backup_recommended,
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
