"""Resource Limits — Define CPU, memory, and disk resource constraints"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResourceLimits:
    """Define resource constraints for sandbox execution."""
    cpu_cores: float = 1.0
    cpu_millis: int = 1000
    memory_mb: int = 512
    memory_gb: float = 0.5
    disk_mb: int = 1024
    disk_gb: float = 1.0
    ephemeral_storage_mb: int = 512
    pids_max: int = 100
    io_read_mbps: float = 100.0
    io_write_mbps: float = 100.0
    gpu_count: int = 0
    gpu_type: str = ""
    network_bandwidth_mbps: float = 100.0

    def to_dict(self) -> dict:
        return {
            "cpu_cores": self.cpu_cores,
            "cpu_millis": self.cpu_millis,
            "memory_mb": self.memory_mb,
            "memory_gb": self.memory_gb,
            "disk_mb": self.disk_mb,
            "disk_gb": self.disk_gb,
            "ephemeral_storage_mb": self.ephemeral_storage_mb,
            "pids_max": self.pids_max,
            "io_read_mbps": self.io_read_mbps,
            "io_write_mbps": self.io_write_mbps,
            "gpu_count": self.gpu_count,
            "gpu_type": self.gpu_type,
            "network_bandwidth_mbps": self.network_bandwidth_mbps,
        }

    def to_docker_args(self) -> list[str]:
        args = [
            f"--cpus={self.cpu_cores}",
            f"--memory={self.memory_mb}m",
            f"--memory-swap={self.memory_mb}m",
            f"--pids-limit={self.pids_max}",
            f"--device-read-bps=/dev/sda:{int(self.io_read_mbps)}mb",
            f"--device-write-bps=/dev/sda:{int(self.io_write_mbps)}mb",
        ]
        return args

    def to_k8s_resources(self) -> dict:
        return {
            "requests": {
                "cpu": f"{self.cpu_millis}m",
                "memory": f"{self.memory_mb}Mi",
                "ephemeral-storage": f"{self.ephemeral_storage_mb}Mi",
            },
            "limits": {
                "cpu": f"{self.cpu_millis}m",
                "memory": f"{self.memory_mb}Mi",
                "ephemeral-storage": f"{self.ephemeral_storage_mb}Mi",
                "pids": str(self.pids_max),
            },
        }

    def to_cgroup_v2(self) -> dict:
        return {
            "cpu.max": f"{int(self.cpu_cores * 100000)} 100000",
            "memory.max": str(self.memory_mb * 1024 * 1024),
            "memory.swap.max": str(self.memory_mb * 1024 * 1024),
            "pids.max": str(self.pids_max),
            "io.max": f"8:0 rbps={int(self.io_read_mbps * 1024 * 1024)} wbps={int(self.io_write_mbps * 1024 * 1024)}",
        }

    @classmethod
    def minimal(cls) -> "ResourceLimits":
        return cls(cpu_cores=0.25, cpu_millis=250, memory_mb=128, disk_mb=256, pids_max=20)

    @classmethod
    def standard(cls) -> "ResourceLimits":
        return cls(cpu_cores=1.0, cpu_millis=1000, memory_mb=512, disk_mb=1024, pids_max=100)

    @classmethod
    def heavy(cls) -> "ResourceLimits":
        return cls(cpu_cores=4.0, cpu_millis=4000, memory_mb=4096, disk_mb=10240, pids_max=500)

    @classmethod
    def restricted(cls) -> "ResourceLimits":
        return cls(
            cpu_cores=0.5, cpu_millis=500, memory_mb=256, disk_mb=512,
            pids_max=50, io_read_mbps=10.0, io_write_mbps=10.0,
        )
