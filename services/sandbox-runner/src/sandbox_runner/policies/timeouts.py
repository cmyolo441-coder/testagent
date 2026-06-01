"""Timeouts — Define execution and idle timeout configurations"""
from dataclasses import dataclass
from enum import Enum


class TimeoutAction(Enum):
    KILL = "kill"
    SIGTERM = "sigterm"
    SIGKILL = "sigkill"
    PAUSE = "pause"
    NOTIFY = "notify"


@dataclass
class TimeoutConfig:
    """Define timeout configurations for sandbox execution."""
    execution_timeout_sec: int = 60
    idle_timeout_sec = 300
    boot_timeout_sec: int = 30
    shutdown_timeout_sec: int = 10
    connection_timeout_sec: int = 10
    read_timeout_sec: int = 30
    write_timeout_sec: int = 30
    cleanup_timeout_sec: int = 5
    max_runtime_sec: int = 3600

    execution_action: TimeoutAction = TimeoutAction.KILL
    idle_action: TimeoutAction = TimeoutAction.SIGTERM

    warn_at_percent: int = 80
    notify_before_sec: int = 5

    def to_dict(self) -> dict:
        return {
            "execution_timeout_sec": self.execution_timeout_sec,
            "idle_timeout_sec": self.idle_timeout_sec,
            "boot_timeout_sec": self.boot_timeout_sec,
            "shutdown_timeout_sec": self.shutdown_timeout_sec,
            "connection_timeout_sec": self.connection_timeout_sec,
            "read_timeout_sec": self.read_timeout_sec,
            "write_timeout_sec": self.write_timeout_sec,
            "cleanup_timeout_sec": self.cleanup_timeout_sec,
            "max_runtime_sec": self.max_runtime_sec,
            "execution_action": self.execution_action.value,
            "idle_action": self.idle_action.value,
            "warn_at_percent": self.warn_at_percent,
        }

    def to_docker_args(self) -> list[str]:
        return [f"--stop-timeout={self.shutdown_timeout_sec}"]

    def to_k8s_lifecycle(self) -> dict:
        return {
            "preStop": {
                "exec": {
                    "command": ["sh", "-c", f"sleep {self.shutdown_timeout_sec}"],
                }
            }
        }

    def get_warning_time(self) -> int:
        return int(self.execution_timeout_sec * self.warn_at_percent / 100)

    def is_expired(self, start_time_sec: float, current_time_sec: float) -> bool:
        elapsed = current_time_sec - start_time_sec
        return elapsed >= self.execution_timeout_sec

    def remaining(self, start_time_sec: float, current_time_sec: float) -> int:
        elapsed = current_time_sec - start_time_sec
        remaining = self.execution_timeout_sec - elapsed
        return max(0, int(remaining))

    @classmethod
    def short(cls) -> "TimeoutConfig":
        return cls(
            execution_timeout_sec=10,
            idle_timeout_sec=30,
            boot_timeout_sec=10,
            shutdown_timeout_sec=3,
            max_runtime_sec=60,
        )

    @classmethod
    def standard(cls) -> "TimeoutConfig":
        return cls(
            execution_timeout_sec=60,
            idle_timeout_sec=300,
            boot_timeout_sec=30,
            shutdown_timeout_sec=10,
            max_runtime_sec=3600,
        )

    @classmethod
    def long_running(cls) -> "TimeoutConfig":
        return cls(
            execution_timeout_sec=600,
            idle_timeout_sec=900,
            boot_timeout_sec=60,
            shutdown_timeout_sec=30,
            max_runtime_sec=86400,
            execution_action=TimeoutAction.SIGTERM,
        )

    @classmethod
    def interactive(cls) -> "TimeoutConfig":
        return cls(
            execution_timeout_sec=1800,
            idle_timeout_sec=600,
            boot_timeout_sec=30,
            shutdown_timeout_sec=10,
            max_runtime_sec=7200,
            execution_action=TimeoutAction.SIGTERM,
            warn_at_percent=90,
        )
