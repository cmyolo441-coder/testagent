"""Namespace Manager — Manage Kubernetes namespaces for sandbox isolation"""
import subprocess
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NamespaceConfig:
    name: str
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    resource_quota: Optional[dict] = None
    network_policy: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "labels": self.labels,
            "annotations": self.annotations,
            "resource_quota": self.resource_quota,
            "network_policy": self.network_policy,
        }


@dataclass
class NamespaceResult:
    success: bool
    name: str
    action: str
    details: str
    uid: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "name": self.name,
            "action": self.action,
            "details": self.details,
            "uid": self.uid,
        }


class NamespaceManager:
    """Manage Kubernetes namespaces for sandbox isolation."""

    SANDBOX_LABEL = {"managed-by": "astra-sandbox-runner"}
    QUOTA_TEMPLATE = {
        "apiVersion": "v1",
        "kind": "ResourceQuota",
        "spec": {
            "hard": {
                "requests.cpu": "2",
                "requests.memory": "2Gi",
                "limits.cpu": "4",
                "limits.memory": "4Gi",
                "pods": "10",
                "services": "5",
                "persistentvolumeclaims": "2",
            }
        },
    }

    def __init__(self, kubectl_bin: str = "kubectl"):
        self.kubectl_bin = kubectl_bin

    def create(self, name: str, labels: dict = None,
               apply_quota: bool = True) -> NamespaceResult:
        merged_labels = {**self.SANDBOX_LABEL, **(labels or {})}

        manifest = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": name,
                "labels": merged_labels,
                "annotations": {
                    "created-by": "astra-sandbox-runner",
                },
            },
        }

        result = self._kubectl_apply(manifest)
        if not result["success"]:
            return NamespaceResult(
                success=False,
                name=name,
                action="create",
                details=result["stderr"],
            )

        uid = self._get_namespace_uid(name)

        if apply_quota:
            self._apply_quota(name)

        return NamespaceResult(
            success=True,
            name=name,
            action="create",
            details=f"Namespace {name} created",
            uid=uid,
        )

    def delete(self, name: str, force: bool = False) -> NamespaceResult:
        try:
            cmd = [self.kubectl_bin, "delete", "namespace", name]
            if force:
                cmd.append("--force")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            return NamespaceResult(
                success=result.returncode == 0,
                name=name,
                action="delete",
                details=result.stdout if result.returncode == 0 else result.stderr,
            )
        except Exception as e:
            return NamespaceResult(
                success=False,
                name=name,
                action="delete",
                details=str(e),
            )

    def list_sandbox_namespaces(self) -> list[dict]:
        try:
            result = subprocess.run(
                [self.kubectl_bin, "get", "namespaces",
                 "-l", "managed-by=astra-sandbox-runner",
                 "-o", "json"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return [
                    {
                        "name": ns["metadata"]["name"],
                        "labels": ns["metadata"].get("labels", {}),
                        "status": ns["status"]["phase"],
                    }
                    for ns in data.get("items", [])
                ]
        except Exception:
            pass
        return []

    def get_namespace_info(self, name: str) -> Optional[dict]:
        try:
            result = subprocess.run(
                [self.kubectl_bin, "get", "namespace", name, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        return None

    def cleanup_old_namespaces(self, max_age_hours: int = 24) -> list[str]:
        cleaned = []
        namespaces = self.list_sandbox_namespaces()
        import time
        now = time.time()

        for ns in namespaces:
            info = self.get_namespace_info(ns["name"])
            if not info:
                continue

            creation = info.get("metadata", {}).get("creationTimestamp", "")
            if creation:
                from datetime import datetime, timezone
                try:
                    created = datetime.fromisoformat(creation.replace("Z", "+00:00"))
                    age_hours = (now - created.timestamp()) / 3600
                    if age_hours > max_age_hours:
                        result = self.delete(ns["name"])
                        if result.success:
                            cleaned.append(ns["name"])
                except Exception:
                    pass

        return cleaned

    def _kubectl_apply(self, manifest: dict) -> dict:
        try:
            import tempfile, os
            import yaml

            path = os.path.join(tempfile.gettempdir(), f"ns-{manifest['metadata']['name']}.yaml")
            with open(path, "w") as f:
                yaml.dump(manifest, f)

            result = subprocess.run(
                [self.kubectl_bin, "apply", "-f", path],
                capture_output=True,
                text=True,
                timeout=15,
            )
            os.remove(path)
            return {"success": result.returncode == 0, "stderr": result.stderr}
        except Exception as e:
            return {"success": False, "stderr": str(e)}

    def _apply_quota(self, namespace: str):
        quota = self.QUOTA_TEMPLATE.copy()
        quota["metadata"] = {"name": "sandbox-quota", "namespace": namespace}
        self._kubectl_apply(quota)

    def _get_namespace_uid(self, name: str) -> str:
        try:
            result = subprocess.run(
                [self.kubectl_bin, "get", "namespace", name,
                 "-o", "jsonpath={.metadata.uid}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip()
        except Exception:
            return ""
