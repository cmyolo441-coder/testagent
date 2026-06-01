"""Filesystem Enforcer — Enforce filesystem access policies"""
import os
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class FilesystemAction(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MODIFY = "modify"
    EXECUTE = "execute"
    LIST = "list"


@dataclass
class FilesystemEnforcementResult:
    allowed: bool
    reason: str
    path: str
    action: FilesystemAction
    policy_name: str
    sandbox_required: bool = False

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "path": self.path,
            "action": self.action.value,
            "policy_name": self.policy_name,
            "sandbox_required": self.sandbox_required,
        }


class FilesystemEnforcer:
    """Enforce filesystem access control policies."""

    def __init__(self):
        self.allowed_paths: list[str] = []
        self.blocked_paths: list[str] = []
        self.allowed_extensions: list[str] = []
        self.blocked_extensions: list[str] = []
        self.max_file_size_bytes: int = 100 * 1024 * 1024  # 100MB
        self._setup_defaults()

    def _setup_defaults(self):
        self.allowed_paths = [
            os.path.expanduser("~"),
            "/tmp",
            "/var/tmp",
            str(Path.cwd()),
        ]
        self.blocked_paths = [
            "/etc", "/usr", "/bin", "/sbin", "/boot", "/root",
            "/proc", "/sys", "/dev", "/lib", "/lib64",
        ]
        self.blocked_extensions = [
            ".key", ".pem", ".p12", ".pfx", ".jks",
        ]

    def enforce(self, operation: str, path: str) -> FilesystemEnforcementResult:
        action = self._parse_action(operation)
        resolved = self._resolve_path(path)

        for blocked in self.blocked_paths:
            if resolved.startswith(blocked) or path.startswith(blocked):
                return FilesystemEnforcementResult(
                    allowed=False,
                    reason=f"Blocked system path: {blocked}",
                    path=path,
                    action=action,
                    policy_name="system_path_protection",
                    sandbox_required=False,
                )

        ext = Path(path).suffix.lower()
        if ext in self.blocked_extensions:
            return FilesystemEnforcementResult(
                allowed=False,
                reason=f"Blocked file extension: {ext}",
                path=path,
                action=action,
                policy_name="extension_block",
            )

        if action in (FilesystemAction.WRITE, FilesystemAction.DELETE, FilesystemAction.MODIFY):
            parent = Path(path).parent
            if parent.exists() and not os.access(str(parent), os.W_OK):
                return FilesystemEnforcementResult(
                    allowed=False,
                    reason="No write permission to parent directory",
                    path=path,
                    action=action,
                    policy_name="permission_check",
                )

        if action == FilesystemAction.DELETE:
            if not Path(path).exists():
                return FilesystemEnforcementResult(
                    allowed=True,
                    reason="File does not exist, nothing to delete",
                    path=path,
                    action=action,
                    policy_name="existence_check",
                )

        if action == FilesystemAction.READ and not Path(path).exists():
            return FilesystemEnforcementResult(
                allowed=False,
                reason=f"File not found: {path}",
                path=path,
                action=action,
                policy_name="existence_check",
            )

        if action == FilesystemAction.EXECUTE:
            if not Path(path).exists():
                return FilesystemEnforcementResult(
                    allowed=False,
                    reason=f"File not found: {path}",
                    path=path,
                    action=action,
                    policy_name="existence_check",
                )
            if not os.access(path, os.X_OK):
                return FilesystemEnforcementResult(
                    allowed=False,
                    reason="No execute permission",
                    path=path,
                    action=action,
                    policy_name="permission_check",
                )

        if ".." in path:
            return FilesystemEnforcementResult(
                allowed=False,
                reason="Path traversal detected",
                path=path,
                action=action,
                policy_name="path_traversal_block",
            )

        return FilesystemEnforcementResult(
            allowed=True,
            reason="Access allowed",
            path=path,
            action=action,
            policy_name="default_allow",
        )

    def _parse_action(self, operation: str) -> FilesystemAction:
        op_lower = operation.lower()
        if any(w in op_lower for w in ("delete", "remove", "unlink", "shred")):
            return FilesystemAction.DELETE
        if any(w in op_lower for w in ("write", "create", "append", "truncate")):
            return FilesystemAction.WRITE
        if any(w in op_lower for w in ("chmod", "chown", "rename", "move")):
            return FilesystemAction.MODIFY
        if any(w in op_lower for w in ("execute", "run", "exec")):
            return FilesystemAction.EXECUTE
        if any(w in op_lower for w in ("list", "ls", "dir", "readdir")):
            return FilesystemAction.LIST
        return FilesystemAction.READ

    def _resolve_path(self, path: str) -> str:
        try:
            return str(Path(path).resolve())
        except Exception:
            return path

    def add_allowed_path(self, path: str):
        self.allowed_paths.append(path)

    def add_blocked_path(self, path: str):
        self.blocked_paths.append(path)
