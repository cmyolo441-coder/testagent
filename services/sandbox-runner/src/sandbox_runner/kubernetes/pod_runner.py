"""Pod Runner — Execute commands in Kubernetes pods"""
import subprocess
import json
import time
import uuid
import yaml
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
import tempfile
import os


@dataclass
class PodLimits:
    cpu_request: str = "100m"
    cpu_limit: str = "500m"
    memory_request: str = "128Mi"
    memory_limit: str = "512Mi"
    ephemeral_storage_request: str = "100Mi"
    ephemeral_storage_limit: str = "500Mi"
    pids_limit: int = 50

    def to_k8s_resources(self) -> dict:
        return {
            "requests": {
                "cpu": self.cpu_request,
                "memory": self.memory_request,
                "ephemeral-storage": self.ephemeral_storage_request,
            },
            "limits": {
                "cpu": self.cpu_limit,
                "memory": self.memory_limit,
                "ephemeral-storage": self.ephemeral_storage_limit,
                "pids": str(self.pids_limit),
            },
        }


@dataclass
class PodResult:
    pod_name: str
    namespace: str
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    container_status: str
    limits: dict

    def to_dict(self) -> dict:
        return {
            "pod_name": self.pod_name,
            "namespace": self.namespace,
            "success": self.success,
            "stdout": self.stdout[:2000],
            "stderr": self.stderr[:1000],
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "container_status": self.container_status,
            "limits": self.limits,
        }


class PodRunner:
    """Execute commands in isolated Kubernetes pods."""

    DEFAULT_IMAGE = "python:3.12-slim"
    DEFAULT_NAMESPACE = "sandbox"

    def __init__(self, kubectl_bin: str = "kubectl"):
        self.kubectl_bin = kubectl_bin
        self._active_pods: list[str] = []

    def run(self, command: str, image: str = None, namespace: str = None,
            limits: PodLimits = None, timeout: int = 60,
            env: dict = None) -> PodResult:
        image = image or self.DEFAULT_IMAGE
        namespace = namespace or self.DEFAULT_NAMESPACE
        limits = limits or PodLimits()
        pod_name = f"sandbox-{uuid.uuid4().hex[:8]}"

        start_time = time.time()

        try:
            pod_manifest = self._create_pod_manifest(
                pod_name, namespace, image, limits, command, env
            )
            manifest_path = self._write_manifest(pod_manifest)

            create_result = self._kubectl_apply(manifest_path, namespace)
            if not create_result["success"]:
                return PodResult(
                    pod_name=pod_name,
                    namespace=namespace,
                    success=False,
                    stdout="",
                    stderr=f"Failed to create pod: {create_result['stderr']}",
                    exit_code=-1,
                    duration_ms=(time.time() - start_time) * 1000,
                    container_status="failed",
                    limits={},
                )

            self._wait_for_pod(pod_name, namespace, timeout)

            logs = self._kubectl_logs(pod_name, namespace)
            exit_code = self._kubectl_exec_exit_code(pod_name, namespace)

            container_status = self._kubectl_get_status(pod_name, namespace)
            duration = (time.time() - start_time) * 1000

            return PodResult(
                pod_name=pod_name,
                namespace=namespace,
                success=exit_code == 0,
                stdout=logs.get("stdout", ""),
                stderr=logs.get("stderr", ""),
                exit_code=exit_code,
                duration_ms=duration,
                container_status=container_status,
                limits={
                    "cpu_limit": limits.cpu_limit,
                    "memory_limit": limits.memory_limit,
                },
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return PodResult(
                pod_name=pod_name,
                namespace=namespace,
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                duration_ms=duration,
                container_status="error",
                limits={},
            )
        finally:
            self._cleanup_pod(pod_name, namespace)
            if pod_name in self._active_pods:
                self._active_pods.remove(pod_name)

    def run_batch(self, commands: list[str], image: str = None,
                  namespace: str = None, limits: PodLimits = None,
                  parallel: bool = False) -> list[PodResult]:
        if parallel:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(self.run, cmd, image, namespace, limits)
                    for cmd in commands
                ]
                return [f.result() for f in concurrent.futures.as_completed(futures)]
        else:
            return [self.run(cmd, image, namespace, limits) for cmd in commands]

    def _create_pod_manifest(self, name: str, namespace: str, image: str,
                              limits: PodLimits, command: str,
                              env: dict = None) -> dict:
        container_env = []
        if env:
            for k, v in env.items():
                container_env.append({"name": k, "value": str(v)})

        manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": name,
                "namespace": namespace,
                "labels": {
                    "app": "sandbox",
                    "managed-by": "astra-sandbox-runner",
                },
            },
            "spec": {
                "restartPolicy": "Never",
                "terminationGracePeriodSeconds": 5,
                "containers": [
                    {
                        "name": "sandbox",
                        "image": image,
                        "command": ["sh", "-c", command],
                        "env": container_env if container_env else [],
                        "resources": limits.to_k8s_resources(),
                        "securityContext": {
                            "readOnlyRootFilesystem": True,
                            "allowPrivilegeEscalation": False,
                            "runAsNonRoot": True,
                            "runAsUser": 65534,
                            "capabilities": {"drop": ["ALL"]},
                        },
                    }
                ],
            },
        }
        return manifest

    def _write_manifest(self, manifest: dict) -> str:
        path = os.path.join(tempfile.gettempdir(), f"pod-{uuid.uuid4().hex[:8]}.yaml")
        with open(path, "w") as f:
            yaml.dump(manifest, f)
        return path

    def _kubectl_apply(self, manifest_path: str, namespace: str) -> dict:
        try:
            result = subprocess.run(
                [self.kubectl_bin, "apply", "-f", manifest_path, "-n", namespace],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e)}

    def _wait_for_pod(self, name: str, namespace: str, timeout: int):
        try:
            subprocess.run(
                [self.kubectl_bin, "wait", "--for=condition=Ready",
                 f"pod/{name}", "-n", namespace, f"--timeout={timeout}s"],
                capture_output=True,
                text=True,
                timeout=timeout + 5,
            )
        except Exception:
            pass

    def _kubectl_logs(self, name: str, namespace: str) -> dict:
        try:
            result = subprocess.run(
                [self.kubectl_bin, "logs", name, "-n", namespace, "--all-containers"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return {"stdout": result.stdout, "stderr": result.stderr}
        except Exception:
            return {"stdout": "", "stderr": ""}

    def _kubectl_exec_exit_code(self, name: str, namespace: str) -> int:
        try:
            result = subprocess.run(
                [self.kubectl_bin, "exec", name, "-n", namespace, "--", "echo", "$?"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            try:
                return int(result.stdout.strip())
            except ValueError:
                return 0 if result.returncode == 0 else 1
        except Exception:
            return -1

    def _kubectl_get_status(self, name: str, namespace: str) -> str:
        try:
            result = subprocess.run(
                [self.kubectl_bin, "get", "pod", name, "-n", namespace,
                 "-o", "jsonpath={.status.phase}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip() or "unknown"
        except Exception:
            return "unknown"

    def _cleanup_pod(self, name: str, namespace: str):
        try:
            subprocess.run(
                [self.kubectl_bin, "delete", "pod", name, "-n", namespace,
                 "--grace-period=0", "--force"],
                capture_output=True,
                timeout=15,
            )
        except Exception:
            pass

            for path in Path(tempfile.gettempdir()).glob(f"pod-*.yaml"):
                try:
                    path.unlink()
                except Exception:
                    pass
