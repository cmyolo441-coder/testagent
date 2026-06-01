"""MicroVM Runner — Execute commands in Firecracker microVMs"""
import subprocess
import json
import time
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class MicroVMLimits:
    vcpu_count: int = 1
    mem_size_mib: int = 256
    disk_size_mib: int = 1024
    boot_args: str = "console=ttyS0 reboot=k panic=1 pci=off"
    kernel_path: str = "/opt/firecracker/vmlinux"
    rootfs_path: str = "/opt/firecracker/rootfs.ext4"
    enable_network: bool = False
    enable_iommu: bool = False

    def to_firecracker_config(self) -> dict:
        return {
            "boot-source": {
                "kernel_image_path": self.kernel_path,
                "boot_args": self.boot_args,
            },
            "drives": [
                {
                    "drive_id": "rootfs",
                    "path_on_host": self.rootfs_path,
                    "is_root_device": True,
                    "is_read_only": False,
                }
            ],
            "machine-config": {
                "vcpu_count": self.vcpu_count,
                "mem_size_mib": self.mem_size_mib,
            },
        }


@dataclass
class MicroVMResult:
    vm_id: str
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    boot_time_ms: float
    limits: dict

    def to_dict(self) -> dict:
        return {
            "vm_id": self.vm_id,
            "success": self.success,
            "stdout": self.stdout[:2000],
            "stderr": self.stderr[:1000],
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "boot_time_ms": self.boot_time_ms,
            "limits": self.limits,
        }


class MicroVMRunner:
    """Execute commands in Firecracker microVMs for strong isolation."""

    def __init__(self, firecracker_bin: str = "firecracker",
                 jailer_bin: str = "jailer"):
        self.firecracker_bin = firecracker_bin
        self.jailer_bin = jailer_bin
        self._running_vms: dict[str, dict] = {}

    def run(self, command: str, limits: MicroVMLimits = None,
            timeout: int = 60) -> MicroVMResult:
        limits = limits or MicroVMLimits()
        vm_id = f"vm-{int(time.time())}-{os.getpid()}"

        start_time = time.time()

        try:
            config = limits.to_firecracker_config()
            config_path = self._write_config(vm_id, config)

            boot_start = time.time()
            boot_result = self._boot_vm(vm_id, config_path, timeout)
            boot_time = (time.time() - boot_start) * 1000

            if not boot_result["success"]:
                return MicroVMResult(
                    vm_id=vm_id,
                    success=False,
                    stdout="",
                    stderr=f"VM boot failed: {boot_result.get('error', 'unknown')}",
                    exit_code=-1,
                    duration_ms=(time.time() - start_time) * 1000,
                    boot_time_ms=boot_time,
                    limits={"vcpu": limits.vcpu_count, "mem_mib": limits.mem_size_mib},
                )

            exec_result = self._execute_in_vm(vm_id, command, timeout)
            duration = (time.time() - start_time) * 1000

            return MicroVMResult(
                vm_id=vm_id,
                success=exec_result["success"],
                stdout=exec_result.get("stdout", ""),
                stderr=exec_result.get("stderr", ""),
                exit_code=exec_result.get("exit_code", -1),
                duration_ms=duration,
                boot_time_ms=boot_time,
                limits={"vcpu": limits.vcpu_count, "mem_mib": limits.mem_size_mib},
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return MicroVMResult(
                vm_id=vm_id,
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                duration_ms=duration,
                boot_time_ms=0,
                limits={"vcpu": limits.vcpu_count, "mem_mib": limits.mem_size_mib},
            )
        finally:
            self._shutdown_vm(vm_id)
            self._cleanup(vm_id)

    def _boot_vm(self, vm_id: str, config_path: str, timeout: int) -> dict:
        try:
            api_socket = f"/tmp/firecracker-{vm_id}.sock"

            result = subprocess.run(
                [self.firecracker_bin, "--api-sock", api_socket, "--config-file", config_path],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {"success": result.returncode == 0, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_in_vm(self, vm_id: str, command: str, timeout: int) -> dict:
        try:
            result = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no",
                 "-o", f"ConnectTimeout={timeout}",
                 f"root@localhost", command],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "exit_code": -1}

    def _shutdown_vm(self, vm_id: str):
        try:
            api_socket = f"/tmp/firecracker-{vm_id}.sock"
            if os.path.exists(api_socket):
                subprocess.run(
                    ["curl", "-X", "PUT", f"http://localhost/boot-source"],
                    capture_output=True,
                    timeout=5,
                )
        except Exception:
            pass

    def _cleanup(self, vm_id: str):
        try:
            api_socket = f"/tmp/firecracker-{vm_id}.sock"
            config_path = f"/tmp/firecracker-config-{vm_id}.json"
            for path in [api_socket, config_path]:
                if os.path.exists(path):
                    os.remove(path)
        except Exception:
            pass

    def _write_config(self, vm_id: str, config: dict) -> str:
        config_path = f"/tmp/firecracker-config-{vm_id}.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        return config_path

    def get_running_vms(self) -> dict[str, dict]:
        return dict(self._running_vms)
