"""Docker Runner — Execute commands in Docker containers"""
import subprocess
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DockerLimits:
    cpu_count: int = 1
    cpu_period: int = 100000
    cpu_quota: int = 50000
    memory_mb: int = 512
    memory_swap_mb: int = 512
    pids_limit: int = 100
    disk_mb: int = 1024
    network_disabled: bool = False
    read_only_rootfs: bool = False
    no_new_privileges: bool = True
    cap_drop: list[str] = field(default_factory=lambda: ["ALL"])
    cap_add: list[str] = field(default_factory=list)

    def to_docker_args(self) -> list[str]:
        args = [
            f"--cpus={self.cpu_count}",
            f"--memory={self.memory_mb}m",
            f"--memory-swap={self.memory_swap_mb}m",
            f"--pids-limit={self.pids_limit}",
            f"--cpu-period={self.cpu_period}",
            f"--cpu-quota={self.cpu_quota}",
        ]
        if self.network_disabled:
            args.append("--network=none")
        if self.read_only_rootfs:
            args.append("--read-only")
        if self.no_new_privileges:
            args.append("--security-opt=no-new-privileges")
        for cap in self.cap_drop:
            args.append(f"--cap-drop={cap}")
        for cap in self.cap_add:
            args.append(f"--cap-add={cap}")
        return args


@dataclass
class DockerResult:
    container_id: str
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    image: str
    command: str
    limits: dict
    oom_killed: bool = False

    def to_dict(self) -> dict:
        return {
            "container_id": self.container_id,
            "success": self.success,
            "stdout": self.stdout[:2000],
            "stderr": self.stderr[:1000],
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "image": self.image,
            "command": self.command,
            "limits": self.limits,
            "oom_killed": self.oom_killed,
        }


class DockerRunner:
    """Execute commands in isolated Docker containers."""

    DEFAULT_IMAGE = "python:3.12-slim"
    CLEANUP_TIMEOUT = 5

    def __init__(self, docker_bin: str = "docker"):
        self.docker_bin = docker_bin
        self._running_containers: list[str] = []

    def run(self, command: str, image: str = None,
            limits: DockerLimits = None, timeout: int = 60,
            volumes: list[dict] = None, env: dict = None,
            working_dir: str = "/workspace") -> DockerResult:
        image = image or self.DEFAULT_IMAGE
        limits = limits or DockerLimits()
        container_id = f"sandbox-{uuid.uuid4().hex[:8]}"

        docker_cmd = [self.docker_bin, "run", "--rm", "--name", container_id]

        docker_cmd.extend(limits.to_docker_args())

        docker_cmd.extend(["-w", working_dir])

        if env:
            for k, v in env.items():
                docker_cmd.extend(["-e", f"{k}={v}"])

        if volumes:
            for vol in volumes:
                src = vol.get("source", "")
                dst = vol.get("target", "")
                ro = ":ro" if vol.get("read_only", False) else ""
                if src and dst:
                    docker_cmd.extend(["-v", f"{src}:{dst}{ro}"])

        docker_cmd.append(image)
        docker_cmd.extend(["sh", "-c", command])

        self._running_containers.append(container_id)
        start_time = time.time()

        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 5,
            )
            duration = (time.time() - start_time) * 1000

            oom_killed = "oom" in result.stderr.lower() or result.returncode == 137

            return DockerResult(
                container_id=container_id,
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                duration_ms=duration,
                image=image,
                command=command,
                limits={
                    "cpu": limits.cpu_count,
                    "memory_mb": limits.memory_mb,
                    "pids_limit": limits.pids_limit,
                },
                oom_killed=oom_killed,
            )
        except subprocess.TimeoutExpired:
            duration = (time.time() - start_time) * 1000
            self._kill_container(container_id)
            return DockerResult(
                container_id=container_id,
                success=False,
                stdout="",
                stderr=f"Execution timed out after {timeout}s",
                exit_code=-1,
                duration_ms=duration,
                image=image,
                command=command,
                limits={"cpu": limits.cpu_count, "memory_mb": limits.memory_mb},
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return DockerResult(
                container_id=container_id,
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                duration_ms=duration,
                image=image,
                command=command,
                limits={"cpu": limits.cpu_count, "memory_mb": limits.memory_mb},
            )
        finally:
            if container_id in self._running_containers:
                self._running_containers.remove(container_id)

    def run_interactive(self, command: str, image: str = None,
                        limits: DockerLimits = None) -> DockerResult:
        image = image or self.DEFAULT_IMAGE
        limits = limits or DockerLimits()
        container_id = f"sandbox-interactive-{uuid.uuid4().hex[:8]}"

        docker_cmd = [self.docker_bin, "run", "-it", "--rm", "--name", container_id]
        docker_cmd.extend(limits.to_docker_args())
        docker_cmd.append(image)
        docker_cmd.extend(["sh", "-c", command])

        try:
            result = subprocess.run(docker_cmd, timeout=300)
            return DockerResult(
                container_id=container_id,
                success=result.returncode == 0,
                stdout="",
                stderr="",
                exit_code=result.returncode,
                duration_ms=0,
                image=image,
                command=command,
                limits={},
            )
        except Exception as e:
            return DockerResult(
                container_id=container_id,
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                duration_ms=0,
                image=image,
                command=command,
                limits={},
            )

    def list_containers(self, all_containers: bool = False) -> list[dict]:
        try:
            cmd = [self.docker_bin, "ps", "--format", "json"]
            if all_containers:
                cmd.append("-a")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            containers = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    containers.append(json.loads(line))
            return containers
        except Exception:
            return []

    def cleanup(self):
        for cid in self._running_containers[:]:
            self._kill_container(cid)

    def _kill_container(self, container_id: str):
        try:
            subprocess.run(
                [self.docker_bin, "kill", container_id],
                capture_output=True,
                timeout=self.CLEANUP_TIMEOUT,
            )
        except Exception:
            pass
