"""Tool Commands — shell, filesystem operations"""
import click
import subprocess
import os
from pathlib import Path
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading
from safety_engine.risk.risk_model import RiskAssessor
from safety_engine.approvals.approval_store import ApprovalStore


def register(cli_group):
    @cli_group.command("shell")
    @click.argument("command")
    @click.option("--timeout", "-t", default=30, help="Timeout in seconds")
    @click.pass_context
    def shell_exec(ctx, command: str, timeout: int):
        """Execute a shell command with risk assessment"""
        astra_ctx = ctx.obj
        risk = RiskAssessor()
        risk_score = risk.assess_command(command)

        if risk_score >= 80:
            error(f"BLOCKED — Risk score too high: {risk_score}/100")
            info(f"Command: {command}")
            info("Use --force to override (requires approval)")
            return

        if astra_ctx.dry_run:
            info(f"DRY RUN — Would execute: {command}")
            info(f"Risk score: {risk_score}/100")
            return

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(astra_ctx.workspace),
            )
            if result.stdout:
                click.echo(result.stdout, nl=False)
            if result.stderr:
                error(result.stderr.strip())
            if result.returncode != 0:
                error(f"Exit code: {result.returncode}")
        except subprocess.TimeoutExpired:
            error(f"Command timed out after {timeout}s")
        except Exception as e:
            error(f"Execution failed: {e}")

    @cli_group.command("ls")
    @click.argument("path", default=".")
    @click.pass_context
    def ls_cmd(ctx, path: str):
        """List directory contents"""
        astra_ctx = ctx.obj
        full_path = astra_ctx.workspace / path
        if not full_path.exists():
            error(f"Path not found: {path}")
            return
        items = sorted(full_path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        for item in items:
            prefix = "[dir] " if item.is_dir() else "      "
            click.echo(f"{prefix}{item.name}")

    @cli_group.command("read")
    @click.argument("path")
    @click.option("--limit", "-l", default=None, type=int, help="Limit lines")
    @click.pass_context
    def read_file(ctx, path: str, limit: int | None):
        """Read a file"""
        astra_ctx = ctx.obj
        full_path = astra_ctx.workspace / path
        if not full_path.exists():
            error(f"File not found: {path}")
            return
        try:
            content = full_path.read_text()
            if limit:
                lines = content.split("\n")[:limit]
                content = "\n".join(lines)
            click.echo(content)
        except Exception as e:
            error(f"Read failed: {e}")

    @cli_group.command("write")
    @click.argument("path")
    @click.argument("content")
    @click.option("--overwrite", is_flag=True, help="Overwrite existing file")
    @click.pass_context
    def write_file(ctx, path: str, content: str, overwrite: bool):
        """Write content to a file"""
        astra_ctx = ctx.obj
        full_path = astra_ctx.workspace / path

        risk = RiskAssessor()
        risk_score = risk.assess_file_write(path)
        if risk_score >= 80:
            error(f"BLOCKED — File write risk too high: {risk_score}/100")
            return

        if full_path.exists() and not overwrite:
            error(f"File exists: {path}. Use --overwrite")
            return

        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        success(f"Written: {path}")

    @cli_group.command("mkdir")
    @click.argument("path")
    @click.pass_context
    def mkdir_cmd(ctx, path: str):
        """Create a directory"""
        astra_ctx = ctx.obj
        full_path = astra_ctx.workspace / path
        full_path.mkdir(parents=True, exist_ok=True)
        success(f"Directory created: {path}")
