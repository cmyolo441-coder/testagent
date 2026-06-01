"""Network Enforcer — Enforce network access policies"""
import re
from dataclasses import dataclass
from enum import Enum


class NetworkAction(Enum):
    CONNECT = "connect"
    LISTEN = "listen"
    SEND = "send"
    RECEIVE = "receive"
    RESOLVE = "resolve"
    TUNNEL = "tunnel"


@dataclass
class NetworkEnforcementResult:
    allowed: bool
    reason: str
    target: str
    action: NetworkAction
    policy_name: str
    port: int = 0

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "target": self.target,
            "action": self.action.value,
            "policy_name": self.policy_name,
            "port": self.port,
        }


class NetworkEnforcer:
    """Enforce network access control policies."""

    def __init__(self):
        self.allowed_hosts: list[str] = []
        self.blocked_hosts: list[str] = []
        self.allowed_ports: list[int] = []
        self.blocked_ports: list[int] = []
        self.blocked_protocols: list[str] = []
        self._setup_defaults()

    def _setup_defaults(self):
        self.blocked_hosts = [
            "169.254.169.254",  # AWS metadata
            "metadata.google.internal",  # GCP metadata
            "169.254.169.254.nip.io",  # Azure metadata
        ]
        self.blocked_ports = [25]  # SMTP often abused for spam
        self.blocked_protocols = ["telnet"]

    def enforce(self, operation: str, target: str) -> NetworkEnforcementResult:
        action = self._parse_action(operation)
        host = self._extract_host(target)
        port = self._extract_port(target)

        for blocked_host in self.blocked_hosts:
            if blocked_host in host or blocked_host in target:
                return NetworkEnforcementResult(
                    allowed=False,
                    reason=f"Blocked metadata/admin endpoint: {blocked_host}",
                    target=target,
                    action=action,
                    policy_name="metadata_protection",
                )

        for blocked_port in self.blocked_ports:
            if port == blocked_port:
                return NetworkEnforcementResult(
                    allowed=False,
                    reason=f"Blocked port: {blocked_port}",
                    target=target,
                    action=action,
                    policy_name="port_block",
                    port=port,
                )

        for protocol in self.blocked_protocols:
            if protocol in target.lower() or protocol in operation.lower():
                return NetworkEnforcementResult(
                    allowed=False,
                    reason=f"Blocked protocol: {protocol}",
                    target=target,
                    action=action,
                    policy_name="protocol_block",
                )

        if action == NetworkAction.LISTEN:
            if port and port < 1024:
                return NetworkEnforcementResult(
                    allowed=False,
                    reason=f"Cannot bind to privileged port: {port}",
                    target=target,
                    action=action,
                    policy_name="privileged_port",
                    port=port,
                )
            if target.startswith("0.0.0.0") or target.startswith("*"):
                return NetworkEnforcementResult(
                    allowed=False,
                    reason="Cannot bind to all interfaces",
                    target=target,
                    action=action,
                    policy_name="interface_binding",
                )

        if action == NetworkAction.TUNNEL:
            return NetworkEnforcementResult(
                allowed=False,
                reason="Tunneling not permitted",
                target=target,
                action=action,
                policy_name="tunnel_block",
            )

        if ".." in target or "//" in target.replace("://", ""):
            return NetworkEnforcementResult(
                allowed=False,
                reason="Invalid target format",
                target=target,
                action=action,
                policy_name="input_validation",
            )

        if self.allowed_hosts:
            allowed = any(ah in host for ah in self.allowed_hosts)
            if not allowed:
                return NetworkEnforcementResult(
                    allowed=False,
                    reason=f"Host not in allowlist: {host}",
                    target=target,
                    action=action,
                    policy_name="host_allowlist",
                )

        return NetworkEnforcementResult(
            allowed=True,
            reason="Network access allowed",
            target=target,
            action=action,
            policy_name="default_allow",
            port=port,
        )

    def _parse_action(self, operation: str) -> NetworkAction:
        op_lower = operation.lower()
        if any(w in op_lower for w in ("listen", "bind", "server")):
            return NetworkAction.LISTEN
        if any(w in op_lower for w in ("send", "post", "upload", "write")):
            return NetworkAction.SEND
        if any(w in op_lower for w in ("recv", "get", "download", "read")):
            return NetworkAction.RECEIVE
        if any(w in op_lower for w in ("resolve", "dns", "lookup")):
            return NetworkAction.RESOLVE
        if any(w in op_lower for w in ("tunnel", "proxy", "forward")):
            return NetworkAction.TUNNEL
        return NetworkAction.CONNECT

    def _extract_host(self, target: str) -> str:
        match = re.search(r"(?:https?://)?([^:/\s]+)", target)
        return match.group(1) if match else target

    def _extract_port(self, target: str) -> int:
        match = re.search(r":(\d+)(?:/|$)", target)
        return int(match.group(1)) if match else 0

    def add_allowed_host(self, host: str):
        self.allowed_hosts.append(host)

    def add_blocked_host(self, host: str):
        self.blocked_hosts.append(host)
