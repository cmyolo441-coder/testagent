"""Sandbox Commands — run commands inside an isolated sandbox."""
import click
import subprocess
import shlex
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading
from safety_engine.risk.risk_model import RiskAssessor


def register(group):
    @group.command("run")
    @click.argument("command")
    @click.option("--backend", default="local",
                  type=click.Choice(["local", "docker", "firecracker", "k8s"]),
                  help="Sandbox backend")
    @click.option("--image", default="python:3.11-slim", help="Docker image (when backend=docker)")
    @click.option("--timeout", default=60, type=int)
    @click.option("--no-network", is_flag=True, help="Disable network access (docker)")
    @click.pass_context
    def run(ctx, command, backend, image, timeout, no_network):
        risk = RiskAssessor().assess_command(command)
        info(f"Risk: {risk}/100  Backend: {backend}")
        if backend == "local":
            try:
                r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
                if r.stdout: click.echo(r.stdout, nl=False)
                if r.stderr: error(r.stderr.strip())
                info(f"Exit: {r.returncode}")
            except subprocess.TimeoutExpired:
                error(f"Timeout after {timeout}s")
        elif backend == "docker":
            net = ["--network=none"] if no_network else []
            cmd = ["docker", "run", "--rm", *net, image, "sh", "-c", command]
            info(f"docker> {' '.join(shlex.quote(x) for x in cmd)}")
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
                if r.stdout: click.echo(r.stdout, nl=False)
                if r.stderr: error(r.stderr.strip())
            except FileNotFoundError:
                error("docker not installed")
        elif backend == "firecracker":
            error("firecracker backend: requires KVM + firecracker binary (see services/sandbox-runner/firecracker)")
        elif backend == "k8s":
            error("k8s backend: requires kubectl + cluster (see services/sandbox-runner/kubernetes)")

    @group.command("policy")
    @click.pass_context
    def policy(ctx):
        """Show active sandbox policy summary."""
        from sandbox_runner.policies.resource_limits import default_limits
        info("Default resource limits:")
        for k, v in default_limits().items():
            click.echo(f"  {k}: {v}")
