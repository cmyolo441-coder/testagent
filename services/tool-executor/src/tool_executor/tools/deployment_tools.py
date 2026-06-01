"""Deployment Tools — Deployment and rollback operations"""
import subprocess
import json
import time
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


@dataclass
class DeploymentResult:
    success: bool
    data: dict = field(default_factory=dict)
    error: str = ""
    operation: str = ""
    environment: str = ""
    version: str = ""
    deployment_id: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "operation": self.operation,
            "environment": self.environment,
            "version": self.version,
            "deployment_id": self.deployment_id,
            "duration_ms": self.duration_ms,
        }


class DeploymentTools:
    """Deployment and rollback operations."""

    VALID_ENVIRONMENTS = {"dev", "staging", "production", "test", "canary"}
    VALID_STRATEGIES = {"rolling", "blue-green", "canary", "recreate"}

    def __init__(self):
        self._deployments: list[dict] = []
        self._rollbacks: list[dict] = []

    def deploy(self, service: str, version: str, environment: str,
               strategy: str = "rolling", config: dict = None) -> DeploymentResult:
        start = time.time()

        if environment not in self.VALID_ENVIRONMENTS:
            return DeploymentResult(
                success=False,
                error=f"Invalid environment: {environment}. Must be one of: {self.VALID_ENVIRONMENTS}",
                operation="deploy",
                environment=environment,
                version=version,
            )

        if strategy not in self.VALID_STRATEGIES:
            return DeploymentResult(
                success=False,
                error=f"Invalid strategy: {strategy}. Must be one of: {self.VALID_STRATEGIES}",
                operation="deploy",
                environment=environment,
                version=version,
            )

        deployment_id = f"deploy-{int(time.time())}-{service}"
        deploy_record = {
            "id": deployment_id,
            "service": service,
            "version": version,
            "environment": environment,
            "strategy": strategy,
            "config": config or {},
            "status": "in_progress",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        cmd = self._build_deploy_command(service, version, environment, strategy, config)

        result = self._run_command(cmd, "deploy")
        duration = (time.time() - start) * 1000

        if result["success"]:
            deploy_record["status"] = "success"
            deploy_record["completed_at"] = datetime.now(timezone.utc).isoformat()
        else:
            deploy_record["status"] = "failed"
            deploy_record["error"] = result.get("error", "")

        self._deployments.append(deploy_record)

        return DeploymentResult(
            success=result["success"],
            data=deploy_record,
            error=result.get("error", ""),
            operation="deploy",
            environment=environment,
            version=version,
            deployment_id=deployment_id,
            duration_ms=duration,
        )

    def rollback(self, service: str, environment: str,
                 target_version: str = "", deployment_id: str = "") -> DeploymentResult:
        start = time.time()

        if not deployment_id and not target_version:
            last_deploy = self._find_last_deploy(service, environment)
            if not last_deploy:
                return DeploymentResult(
                    success=False,
                    error="No previous deployment found to rollback to",
                    operation="rollback",
                    environment=environment,
                )
            target_version = last_deploy.get("version", "")
            deployment_id = last_deploy.get("id", "")

        rollback_record = {
            "service": service,
            "environment": environment,
            "target_version": target_version,
            "original_deployment_id": deployment_id,
            "status": "in_progress",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        cmd = ["kubectl", "rollout", "undo", f"deployment/{service}",
               "-n", environment]

        result = self._run_command(cmd, "rollback")
        duration = (time.time() - start) * 1000

        if result["success"]:
            rollback_record["status"] = "success"
            rollback_record["completed_at"] = datetime.now(timezone.utc).isoformat()
        else:
            rollback_record["status"] = "failed"
            rollback_record["error"] = result.get("error", "")

        self._rollbacks.append(rollback_record)

        return DeploymentResult(
            success=result["success"],
            data=rollback_record,
            error=result.get("error", ""),
            operation="rollback",
            environment=environment,
            version=target_version,
            duration_ms=duration,
        )

    def status(self, service: str, environment: str = "") -> DeploymentResult:
        cmd = ["kubectl", "get", f"deployment/{service}",
               "-n", environment or "default", "-o", "json"]

        result = self._run_command(cmd, "status")

        if result["success"]:
            try:
                data = json.loads(result.get("output", "{}"))
                status_info = {
                    "replicas": data.get("status", {}).get("replicas", 0),
                    "ready": data.get("status", {}).get("readyReplicas", 0),
                    "available": data.get("status", {}).get("availableReplicas", 0),
                    "updated": data.get("status", {}).get("updatedReplicas", 0),
                    "strategy": data.get("spec", {}).get("strategy", {}).get("type", ""),
                }
                return DeploymentResult(
                    success=True,
                    data=status_info,
                    operation="status",
                    environment=environment,
                    service=service,
                )
            except json.JSONDecodeError:
                pass

        return DeploymentResult(
            success=result["success"],
            error=result.get("error", ""),
            operation="status",
            environment=environment,
        )

    def scale(self, service: str, replicas: int, environment: str = "default") -> DeploymentResult:
        start = time.time()
        cmd = ["kubectl", "scale", f"deployment/{service}",
               f"--replicas={replicas}", "-n", environment]

        result = self._run_command(cmd, "scale")
        duration = (time.time() - start) * 1000

        return DeploymentResult(
            success=result["success"],
            data={"service": service, "replicas": replicas, "environment": environment},
            error=result.get("error", ""),
            operation="scale",
            environment=environment,
            duration_ms=duration,
        )

    def get_history(self, service: str = None, environment: str = None) -> list[dict]:
        history = self._deployments
        if service:
            history = [d for d in history if d["service"] == service]
        if environment:
            history = [d for d in history if d["environment"] == environment]
        return history

    def get_rollbacks(self) -> list[dict]:
        return list(self._rollbacks)

    def _build_deploy_command(self, service: str, version: str,
                               environment: str, strategy: str,
                               config: dict = None) -> list[str]:
        cmd = ["kubectl", "set", "image", f"deployment/{service}",
               f"{service}={service}:{version}",
               "-n", environment]
        return cmd

    def _find_last_deploy(self, service: str, environment: str) -> Optional[dict]:
        for deploy in reversed(self._deployments):
            if (deploy["service"] == service and
                deploy["environment"] == environment and
                deploy["status"] == "success"):
                return deploy
        return None

    def _run_command(self, cmd: list[str], operation: str) -> dict:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out", "output": ""}
        except Exception as e:
            return {"success": False, "error": str(e), "output": ""}
