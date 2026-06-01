"""Filesystem Limits — Define filesystem access constraints"""
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FilesystemLimits:
    """Define filesystem access constraints for sandbox execution."""
    allowed_paths: list[str] = field(default_factory=list)
    blocked_paths: list[str] = field(default_factory=list)
    read_only_paths: list[str] = field(default_factory=list)
    writable_paths: list[str] = field(default_factory=list)
    max_file_size_mb: int = 100
    max_total_size_mb: int = 1024
    max_file_count: int = 10000
    allow_symlinks: bool = False
    allow_executables: bool = True
    allowed_extensions: list[str] = field(default_factory=list)
    blocked_extensions: list[str] = field(default_factory=list)
    mask_sensitive: bool = True

    def to_dict(self) -> dict:
        return {
            "allowed_paths": self.allowed_paths,
            "blocked_paths": self.blocked_paths,
            "read_only_paths": self.read_only_paths,
            "writable_paths": self.writable_paths,
            "max_file_size_mb": self.max_file_size_mb,
            "max_total_size_mb": self.max_total_size_mb,
            "max_file_count": self.max_file_count,
            "allow_symlinks": self.allow_symlinks,
            "allow_executables": self.allow_executables,
            "allowed_extensions": self.allowed_extensions,
            "blocked_extensions": self.blocked_extensions,
        }

    def to_docker_args(self) -> list[str]:
        args = ["--read-only"]
        tmp_size = min(self.max_total_size_mb, 512)
        args.append(f"--tmpfs /tmp:rw,size={tmp_size}m,noexec,nosuid")
        for path in self.writable_paths:
            args.append(f"--tmpfs {path}:rw,size={min(self.max_file_size_mb, 256)}m")
        return args

    def to_k8s_volumes(self) -> list[dict]:
        volumes = []
        volumes.append({
            "name": "tmp",
            "emptyDir": {"sizeLimit": f"{self.max_total_size_mb}Mi"},
        })
        return volumes

    def to_k8s_volume_mounts(self) -> list[dict]:
        mounts = [{"name": "tmp", "mountPath": "/tmp"}]
        for path in self.writable_paths:
            mounts.append({
                "name": "tmp",
                "mountPath": path,
            })
        return mounts

    def is_path_allowed(self, path: str) -> tuple[bool, str]:
        resolved = self._resolve(path)

        for blocked in self.blocked_paths:
            if resolved.startswith(blocked):
                return False, f"Path is blocked: {blocked}"

        if self.allowed_paths:
            allowed = any(resolved.startswith(ap) for ap in self.allowed_paths)
            if not allowed:
                return False, f"Path not in allowed list"

        ext = Path(path).suffix.lower()
        if self.blocked_extensions and ext in self.blocked_extensions:
            return False, f"Extension blocked: {ext}"
        if self.allowed_extensions and ext not in self.allowed_extensions:
            return False, f"Extension not allowed: {ext}"

        if not self.allow_symlinks and ".." in path:
            return False, "Path traversal not allowed"

        return True, "Path allowed"

    def is_extension_allowed(self, extension: str) -> bool:
        ext = extension.lower() if extension.startswith(".") else f".{extension.lower()}"
        if self.blocked_extensions and ext in self.blocked_extensions:
            return False
        if self.allowed_extensions and ext not in self.allowed_extensions:
            return False
        return True

    def _resolve(self, path: str) -> str:
        try:
            return str(Path(path).resolve())
        except Exception:
            return path

    @classmethod
    def permissive(cls) -> "FilesystemLimits":
        return cls(
            allowed_paths=["/"],
            blocked_paths=["/etc/shadow", "/etc/passwd", "/proc", "/sys"],
            max_file_size_mb=1000,
            max_total_size_mb=10240,
            max_file_count=100000,
            allow_symlinks=True,
        )

    @classmethod
    def restricted(cls) -> "FilesystemLimits":
        return cls(
            allowed_paths=["/workspace", "/tmp"],
            blocked_paths=[
                "/etc", "/usr", "/bin", "/sbin", "/boot", "/root",
                "/proc", "/sys", "/dev", "/lib", "/lib64",
            ],
            writable_paths=["/tmp", "/workspace"],
            max_file_size_mb=50,
            max_total_size_mb=512,
            max_file_count=1000,
            allow_symlinks=False,
            blocked_extensions=[".key", ".pem", ".p12", ".pfx"],
        )

    @classmethod
    def minimal(cls) -> "FilesystemLimits":
        return cls(
            allowed_paths=["/workspace"],
            blocked_paths=["/"],
            writable_paths=["/workspace"],
            max_file_size_mb=10,
            max_total_size_mb=50,
            max_file_count=100,
            allow_symlinks=False,
            allow_executables=False,
        )
