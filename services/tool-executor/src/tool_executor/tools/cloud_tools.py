"""Cloud Tools — Cloud provider operations"""
import subprocess
import json
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CloudResult:
    success: bool
    data: dict = field(default_factory=dict)
    error: str = ""
    provider: str = ""
    service: str = ""
    operation: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "provider": self.provider,
            "service": self.service,
            "operation": self.operation,
            "duration_ms": self.duration_ms,
        }


class CloudTools:
    """Cloud provider operations for AWS, GCP, and Azure."""

    AWS_SERVICES = {
        "s3", "ec2", "lambda", "dynamodb", "iam", "cloudwatch",
        "ecs", "eks", "rds", "sqs", "sns", "kinesis",
    }

    GCP_SERVICES = {
        "compute", "storage", "functions", "bigquery", "pubsub",
        "cloudrun", "gke", "cloudsql", "firestore",
    }

    AZURE_SERVICES = {
        "vm", "blob", "functions", "cosmosdb", "aks",
        "sql", "storage", "eventhub", "keyvault",
    }

    def __init__(self):
        self._command_history: list[dict] = []

    def aws(self, service: str, action: str, args: dict = None,
            region: str = "us-east-1", output: str = "json") -> CloudResult:
        start = time.time()

        if service not in self.AWS_SERVICES:
            return CloudResult(
                success=False,
                error=f"Unknown AWS service: {service}",
                provider="aws",
                service=service,
                operation=action,
            )

        cmd = ["aws", service, action, "--region", region, "--output", output]
        if args:
            for k, v in args.items():
                if isinstance(v, bool):
                    if v:
                        cmd.append(f"--{k}")
                elif v is not None:
                    cmd.extend([f"--{k}", str(v)])

        return self._run_command(cmd, "aws", service, action, start)

    def gcp(self, service: str, action: str, args: dict = None,
            project: str = "", zone: str = "us-central1-a") -> CloudResult:
        start = time.time()

        if service not in self.GCP_SERVICES:
            return CloudResult(
                success=False,
                error=f"Unknown GCP service: {service}",
                provider="gcp",
                service=service,
                operation=action,
            )

        tool_map = {
            "compute": "gcloud compute",
            "storage": "gsutil",
            "functions": "gcloud functions",
            "bigquery": "bq",
            "pubsub": "gcloud pubsub",
            "cloudrun": "gcloud run",
            "gke": "gcloud container",
            "cloudsql": "gcloud sql",
            "firestore": "gcloud firestore",
        }

        base_cmd = tool_map.get(service, f"gcloud {service}")
        cmd = base_cmd.split() + action.split()
        if project:
            cmd.extend(["--project", project])
        if args:
            for k, v in args.items():
                if isinstance(v, bool) and v:
                    cmd.append(f"--{k}")
                elif v is not None:
                    cmd.extend([f"--{k}", str(v)])

        return self._run_command(cmd, "gcp", service, action, start)

    def azure(self, service: str, action: str, args: dict = None,
              resource_group: str = "", subscription: str = "") -> CloudResult:
        start = time.time()

        if service not in self.AZURE_SERVICES:
            return CloudResult(
                success=False,
                error=f"Unknown Azure service: {service}",
                provider="azure",
                service=service,
                operation=action,
            )

        cmd = ["az"]
        service_aliases = {
            "vm": "vm", "blob": "storage blob", "functions": "functionapp",
            "cosmosdb": "cosmosdb", "aks": "aks", "sql": "sql",
            "storage": "storage", "eventhub": "eventhubs", "keyvault": "keyvault",
        }
        az_service = service_aliases.get(service, service)
        cmd.extend(az_service.split())
        cmd.extend(action.split())

        if resource_group:
            cmd.extend(["--resource-group", resource_group])
        if subscription:
            cmd.extend(["--subscription", subscription])

        return self._run_command(cmd, "azure", service, action, start)

    def list_resources(self, provider: str, service: str, **kwargs) -> CloudResult:
        if provider == "aws":
            return self.aws(service, "list", kwargs)
        elif provider == "gcp":
            return self.gcp(service, "list", kwargs)
        elif provider == "azure":
            return self.azure(service, "list", kwargs)
        return CloudResult(
            success=False,
            error=f"Unknown provider: {provider}",
            provider=provider,
            service=service,
            operation="list",
        )

    def get_resource(self, provider: str, service: str,
                     resource_id: str, **kwargs) -> CloudResult:
        if provider == "aws":
            return self.aws(service, "describe", {"resource-ids": [resource_id], **kwargs})
        elif provider == "gcp":
            return self.gcp(service, f"describe {resource_id}", kwargs)
        elif provider == "azure":
            return self.azure(service, f"show --ids {resource_id}", kwargs)
        return CloudResult(
            success=False,
            error=f"Unknown provider: {provider}",
            provider=provider,
            service=service,
            operation="describe",
        )

    def _run_command(self, cmd: list[str], provider: str, service: str,
                     operation: str, start_time: float) -> CloudResult:
        self._command_history.append({
            "provider": provider,
            "service": service,
            "operation": operation,
            "command": " ".join(cmd),
            "timestamp": time.time(),
        })

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            duration = (time.time() - start_time) * 1000

            if result.returncode == 0:
                data = {}
                try:
                    data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    data = {"output": result.stdout[:5000]}

                return CloudResult(
                    success=True,
                    data=data,
                    provider=provider,
                    service=service,
                    operation=operation,
                    duration_ms=duration,
                )
            else:
                return CloudResult(
                    success=False,
                    error=result.stderr[:2000],
                    provider=provider,
                    service=service,
                    operation=operation,
                    duration_ms=duration,
                )
        except FileNotFoundError:
            return CloudResult(
                success=False,
                error=f"Cloud CLI not found for {provider}",
                provider=provider,
                service=service,
                operation=operation,
                duration_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return CloudResult(
                success=False,
                error=str(e),
                provider=provider,
                service=service,
                operation=operation,
                duration_ms=(time.time() - start_time) * 1000,
            )

    def get_history(self) -> list[dict]:
        return list(self._command_history)
