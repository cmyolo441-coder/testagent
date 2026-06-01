"""Volume Policy — Control volume mounts for sandbox containers"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum


class MountMode(Enum):
    READ_ONLY = "ro"
    READ_WRITE = "rw"


@dataclass
class MountRequest:
    source: str
    target: str
    mode: MountMode = MountMode.READ_ONLY
    options: list[str] = field(default_factory=list)

    def to_docker_vol(self) -> str:
        suffix = ":ro" if self.mode == MountMode.READ_ONLY else ""
        return f"{self.source}:{self.target}{suffix}"


@dataclass
class VolumePolicyResult:
    allowed: bool
    reason: str
    mount: MountRequest
    policy_name: str
    sanitized_source: str = ""

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "source": self.mount.source,
            "target": self.mount.target,
            "mode": self.mount.mode.value,
            "policy_name": self.policy_name,
        }


class VolumePolicy:
    """Control and validate volume mounts for sandbox containers."""

    BLOCKED_SOURCE_PATHS = [
        "/etc", "/usr", "/bin", "/sbin", "/boot", "/root",
        "/proc", "/sys", "/dev", "/lib", "/lib64",
        "/var/run/docker.sock",
        "/run/docker.sock",
    ]

    BLOCKED_TARGET_PATHS = [
        "/etc", "/usr", "/bin", "/sbin", "/boot",
        "/proc", "/sys", "/dev", "/root",
    ]

    SENSITIVE_FILES = [
        ".ssh", ".gnupg", ".aws", ".docker", ".kube",
        ".env", ".netrc", ".npmrc", "credentials",
    ]

    MAX_PATH_DEPTH = 10

    def __init__(self):
        self.allowed_source_prefixes: list[str] = [os.path.expanduser("~"), "/tmp", "/workspace"]
        self.allowed_target_prefixes: list[str] = ["/workspace", "/tmp", "/data", "/logs"]
        self.blocked_mounts: list[tuple[str, str]] = []

    def check(self, source: str, target: str, mode: MountMode = MountMode.READ_ONLY) -> VolumePolicyResult:
        mount = MountRequest(source=source, target=target, mode=mode)

        source_resolved = self._resolve(source)

        for blocked in self.BLOCKED_SOURCE_PATHS:
            if source_resolved.startswith(blocked) or source_resolved == blocked:
                return VolumePolicyResult(
                    allowed=False,
                    reason=f"Source path is blocked: {blocked}",
                    mount=mount,
                    policy_name="source_block",
                )

        for blocked in self.BLOCKED_TARGET_PATHS:
            if target.startswith(blocked):
                return VolumePolicyResult(
                    allowed=False,
                    reason=f"Target path is blocked: {blocked}",
                    mount=mount,
                    policy_name="target_block",
                )

        source_name = Path(source).name.lower()
        for sensitive in self.SENSITIVE_FILES:
            if sensitive in source_name:
                return VolumePolicyResult(
                    allowed=False,
                    reason=f"Sensitive file/path: {sensitive}",
                    mount=mount,
                    policy_name="sensitive_data_block",
                )

        if ".." in source or ".." in target:
            return VolumePolicyResult(
                allowed=False,
                reason="Path traversal detected",
                mount=mount,
                policy_name="traversal_block",
            )

        if source.count("/") > self.MAX_PATH_DEPTH or target.count("/") > self.MAX_PATH_DEPTH:
            return VolumePolicyResult(
                allowed=False,
                reason="Path depth exceeds maximum",
                mount=mount,
                policy_name="depth_limit",
            )

        for pair in self.blocked_mounts:
            if pair[0] in source and pair[1] in target:
                return VolumePolicyResult(
                    allowed=False,
                    reason=f"Blocked mount combination: {pair}",
                    mount=mount,
                    policy_name="custom_block",
                )

        if mode == MountMode.READ_WRITE:
            allowed_rw = any(
                source_resolved.startswith(prefix)
                for prefix in self.allowed_source_prefixes
            )
            if not allowed_rw:
                return VolumePolicyResult(
                    allowed=False,
                    reason="Read-write mount not allowed for this source",
                    mount=mount,
                    policy_name="rw_restriction",
                )

        return VolumePolicyResult(
            allowed=True,
            reason="Mount allowed",
            mount=mount,
            policy_name="default_allow",
            sanitized_source=source_resolved,
        )

    def _resolve(self, path: str) -> str:
        try:
            return str(Path(path).resolve())
        except Exception:
            return path

    def add_blocked_mount(self, source_pattern: str, target_pattern: str):
        self.blocked_mounts.append((source_pattern, target_pattern))

    def add_allowed_source(self, prefix: str):
        self.allowed_source_prefixes.append(prefix)
