"""Network Policy — Configure Kubernetes network policies for sandbox isolation"""
import subprocess
import json
import yaml
import tempfile
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NetworkRule:
    name: str
    direction: str  # "ingress" or "egress"
    ports: list[int] = field(default_factory=list)
    protocol: str = "TCP"
    source_namespace: str = ""
    source_pod_selector: dict = field(default_factory=dict)
    dest_namespace: str = ""
    dest_pod_selector: dict = field(default_factory=dict)
    cidr: str = ""

    def to_k8s_rule(self) -> dict:
        rule = {}
        if self.ports:
            rule["ports"] = [{"port": p, "protocol": self.protocol} for p in self.ports]
        if self.cidr:
            if self.direction == "ingress":
                rule["from"] = [{"ipBlock": {"cidr": self.cidr}}]
            else:
                rule["to"] = [{"ipBlock": {"cidr": self.cidr}}]
        if self.source_namespace:
            ns_match = {"namespaceSelector": {"matchLabels": {"name": self.source_namespace}}}
            if self.direction == "ingress":
                rule.setdefault("from", []).append(ns_match)
            else:
                rule.setdefault("to", []).append(ns_match)
        return rule


@dataclass
class PolicyConfig:
    name: str
    namespace: str
    pod_selector: dict = field(default_factory=dict)
    ingress_rules: list[NetworkRule] = field(default_factory=list)
    egress_rules: list[NetworkRule] = field(default_factory=list)
    policy_types: list[str] = field(default_factory=lambda: ["Ingress", "Egress"])

    def to_k8s_manifest(self) -> dict:
        ingress = [r.to_k8s_rule() for r in self.ingress_rules]
        egress = [r.to_k8s_rule() for r in self.egress_rules]

        return {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
            },
            "spec": {
                "podSelector": {"matchLabels": self.pod_selector} if self.pod_selector else {},
                "policyTypes": self.policy_types,
                "ingress": ingress if ingress else [],
                "egress": egress if egress else [],
            },
        }


@dataclass
class PolicyResult:
    success: bool
    name: str
    namespace: str
    action: str
    details: str

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "name": self.name,
            "namespace": self.namespace,
            "action": self.action,
            "details": self.details,
        }


class NetworkPolicy:
    """Configure Kubernetes network policies for sandbox isolation."""

    DENY_ALL_POLICY = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {"name": "deny-all"},
        "spec": {
            "podSelector": {},
            "policyTypes": ["Ingress", "Egress"],
            "ingress": [],
            "egress": [],
        },
    }

    ALLOW_DNS_EGRESS = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {"name": "allow-dns"},
        "spec": {
            "podSelector": {},
            "policyTypes": ["Egress"],
            "egress": [
                {"ports": [{"port": 53, "protocol": "UDP"}, {"port": 53, "protocol": "TCP"}]}
            ],
        },
    }

    def __init__(self, kubectl_bin: str = "kubectl"):
        self.kubectl_bin = kubectl_bin

    def configure(self, namespace: str, rules: list[NetworkRule] = None,
                  deny_all: bool = True, allow_dns: bool = True) -> PolicyResult:
        if deny_all:
            result = self._apply_policy(self.DENY_ALL_POLICY, namespace)
            if not result["success"]:
                return PolicyResult(
                    success=False,
                    name="deny-all",
                    namespace=namespace,
                    action="apply",
                    details=result["stderr"],
                )

        if allow_dns:
            self._apply_policy(self.ALLOW_DNS_EGRESS, namespace)

        if rules:
            ingress_rules = [r for r in rules if r.direction == "ingress"]
            egress_rules = [r for r in rules if r.direction == "egress"]

            config = PolicyConfig(
                name="sandbox-network-rules",
                namespace=namespace,
                ingress_rules=ingress_rules,
                egress_rules=egress_rules,
            )
            manifest = config.to_k8s_manifest()

            result = self._apply_policy(manifest, namespace)
            if not result["success"]:
                return PolicyResult(
                    success=False,
                    name="sandbox-network-rules",
                    namespace=namespace,
                    action="apply",
                    details=result["stderr"],
                )

        return PolicyResult(
            success=True,
            name="sandbox-network-rules",
            namespace=namespace,
            action="configure",
            details=f"Network policy configured for {namespace}",
        )

    def apply_egress_whitelist(self, namespace: str, allowed_hosts: list[str],
                                allowed_ports: list[int] = None) -> PolicyResult:
        allowed_ports = allowed_ports or [443, 80]

        egress_rules = []
        for host in allowed_hosts:
            egress_rules.append(NetworkRule(
                name=f"allow-{host}",
                direction="egress",
                ports=allowed_ports,
                cidr=self._host_to_cidr(host),
            ))

        config = PolicyConfig(
            name="egress-whitelist",
            namespace=namespace,
            egress_rules=egress_rules,
        )

        result = self._apply_policy(config.to_k8s_manifest(), namespace)
        return PolicyResult(
            success=result["success"],
            name="egress-whitelist",
            namespace=namespace,
            action="apply",
            details="Egress whitelist applied" if result["success"] else result["stderr"],
        )

    def remove_policy(self, name: str, namespace: str) -> PolicyResult:
        try:
            result = subprocess.run(
                [self.kubectl_bin, "delete", "networkpolicy", name, "-n", namespace],
                capture_output=True,
                text=True,
                timeout=15,
            )
            return PolicyResult(
                success=result.returncode == 0,
                name=name,
                namespace=namespace,
                action="delete",
                details=result.stdout if result.returncode == 0 else result.stderr,
            )
        except Exception as e:
            return PolicyResult(
                success=False,
                name=name,
                namespace=namespace,
                action="delete",
                details=str(e),
            )

    def list_policies(self, namespace: str) -> list[dict]:
        try:
            result = subprocess.run(
                [self.kubectl_bin, "get", "networkpolicy", "-n", namespace, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return [
                    {
                        "name": p["metadata"]["name"],
                        "namespace": namespace,
                        "pod_selector": p["spec"].get("podSelector", {}),
                        "policy_types": p["spec"].get("policyTypes", []),
                    }
                    for p in data.get("items", [])
                ]
        except Exception:
            pass
        return []

    def _apply_policy(self, manifest: dict, namespace: str) -> dict:
        try:
            name = manifest["metadata"]["name"]
            path = os.path.join(tempfile.gettempdir(), f"netpol-{name}.yaml")
            with open(path, "w") as f:
                yaml.dump(manifest, f)

            result = subprocess.run(
                [self.kubectl_bin, "apply", "-f", path, "-n", namespace],
                capture_output=True,
                text=True,
                timeout=15,
            )
            os.remove(path)
            return {"success": result.returncode == 0, "stderr": result.stderr}
        except Exception as e:
            return {"success": False, "stderr": str(e)}

    def _host_to_cidr(self, host: str) -> str:
        if "/" in host:
            return host
        return f"{host}/32"
