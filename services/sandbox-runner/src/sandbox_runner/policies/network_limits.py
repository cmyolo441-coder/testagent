"""Network Limits — Define network access constraints"""
from dataclasses import dataclass, field
import re


@dataclass
class NetworkLimits:
    """Define network access constraints for sandbox execution."""
    enabled: bool = True
    allowed_hosts: list[str] = field(default_factory=list)
    blocked_hosts: list[str] = field(default_factory=list)
    allowed_ports: list[int] = field(default_factory=list)
    blocked_ports: list[int] = field(default_factory=list)
    allowed_protocols: list[str] = field(default_factory=lambda: ["tcp", "udp"])
    blocked_protocols: list[str] = field(default_factory=list)
    dns_enabled: bool = True
    max_connections: int = 100
    max_bandwidth_mbps: float = 100.0
    allow_localhost: bool = True
    allow_broadcast: bool = False
    allow_multicast: bool = False
    outbound_only: bool = True
    proxy_url: str = ""

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "allowed_hosts": self.allowed_hosts,
            "blocked_hosts": self.blocked_hosts,
            "allowed_ports": self.allowed_ports,
            "blocked_ports": self.blocked_ports,
            "allowed_protocols": self.allowed_protocols,
            "blocked_protocols": self.blocked_protocols,
            "dns_enabled": self.dns_enabled,
            "max_connections": self.max_connections,
            "max_bandwidth_mbps": self.max_bandwidth_mbps,
            "allow_localhost": self.allow_localhost,
            "outbound_only": self.outbound_only,
        }

    def to_docker_args(self) -> list[str]:
        args = []
        if not self.enabled:
            args.append("--network=none")
        elif self.outbound_only:
            args.append("--network=bridge")
        if self.proxy_url:
            args.extend(["-e", f"http_proxy={self.proxy_url}"])
            args.extend(["-e", f"https_proxy={self.proxy_url}"])
        return args

    def to_k8s_network_policy(self) -> dict:
        egress_rules = []
        if self.allowed_hosts:
            for host in self.allowed_hosts:
                rule = {"to": [{"ipBlock": {"cidr": f"{host}/32"}}]}
                if self.allowed_ports:
                    rule["ports"] = [{"port": p, "protocol": "TCP"} for p in self.allowed_ports]
                egress_rules.append(rule)

        return {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "spec": {
                "egress": egress_rules if egress_rules else [],
                "ingress": [] if self.outbound_only else [{"from": []}],
            },
        }

    def is_host_allowed(self, host: str) -> tuple[bool, str]:
        if not self.enabled:
            return False, "Networking disabled"

        host_lower = host.lower().strip()

        for blocked in self.blocked_hosts:
            if blocked in host_lower:
                return False, f"Host blocked: {blocked}"

        localhost_patterns = ["localhost", "127.0.0.1", "::1", "0.0.0.0"]
        if any(lp in host_lower for lp in localhost_patterns):
            if not self.allow_localhost:
                return False, "Localhost access denied"

        if self.allowed_hosts:
            allowed = any(ah in host_lower for ah in self.allowed_hosts)
            if not allowed:
                return False, f"Host not in allowlist: {host}"

        return True, "Host allowed"

    def is_port_allowed(self, port: int) -> tuple[bool, str]:
        if not self.enabled:
            return False, "Networking disabled"

        if port in self.blocked_ports:
            return False, f"Port blocked: {port}"

        if self.allowed_ports and port not in self.allowed_ports:
            return False, f"Port not in allowlist: {port}"

        return True, "Port allowed"

    def is_protocol_allowed(self, protocol: str) -> tuple[bool, str]:
        proto = protocol.lower()

        if proto in self.blocked_protocols:
            return False, f"Protocol blocked: {proto}"

        if self.allowed_protocols and proto not in self.allowed_protocols:
            return False, f"Protocol not allowed: {proto}"

        return True, "Protocol allowed"

    @classmethod
    def full_access(cls) -> "NetworkLimits":
        return cls(enabled=True, allowed_hosts=["*"], allowed_ports=list(range(1, 65536)))

    @classmethod
    def outbound_only(cls) -> "NetworkLimits":
        return cls(
            enabled=True,
            outbound_only=True,
            allow_localhost=False,
            allow_broadcast=False,
            blocked_ports=[25, 587],
        )

    @classmethod
    def restricted(cls) -> "NetworkLimits":
        return cls(
            enabled=True,
            outbound_only=True,
            allowed_ports=[80, 443, 8080, 8443],
            allowed_hosts=["github.com", "pypi.org", "registry.npmjs.org"],
            allow_localhost=False,
            max_connections=20,
        )

    @classmethod
    def disabled(cls) -> "NetworkLimits":
        return cls(enabled=False)
