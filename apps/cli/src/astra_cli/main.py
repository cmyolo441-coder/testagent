"""ASTRA CLI — Main Entry Point"""
import click
from rich.console import Console
from astra_cli.path_bootstrap import bootstrap_paths
from astra_cli.context import AstraContext

bootstrap_paths()

console = Console()
pass_context = click.make_pass_decorator(AstraContext, ensure=True)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--dry-run", is_flag=True, help="Simulate without executing")
@click.option("--workspace", "-w", type=click.Path(), default=None, help="Workspace path")
@click.version_option(version="0.1.0", prog_name="astra")
@pass_context
def cli(ctx: AstraContext, verbose: bool, dry_run: bool, workspace: str | None):
    """ASTRA Command OS — Civilization-Scale Terminal AI Agent"""
    ctx.verbose = verbose
    ctx.dry_run = dry_run
    if workspace:
        from pathlib import Path
        ctx.workspace = Path(workspace)
    ctx.ensure_dirs()


@cli.command()
@pass_context
def dashboard(ctx: AstraContext):
    """Show mission control dashboard"""
    from astra_cli.commands.dashboard import show_dashboard
    show_dashboard(ctx)


@cli.command()
@pass_context
def tui(ctx: AstraContext):
    """Launch the full beautiful terminal UI."""
    try:
        from astra_tui.app import AstraTUI
    except Exception as e:
        click.echo(f"TUI unavailable: {e}\nInstall with: pip install astra-command-os[tui]")
        return
    AstraTUI().run()


# Top-level command groups
@cli.group()
def mission():
    """Mission management commands"""

@cli.group()
def tool():
    """Tool execution commands"""

@cli.group()
def agent():
    """Agent runtime commands"""

@cli.group()
def memory():
    """Memory operations"""

@cli.group()
def verify():
    """Truth verification commands"""

@cli.group()
def approval():
    """Approval management"""

@cli.group()
def sandbox():
    """Sandbox execution"""

@cli.group()
def science():
    """Science engine commands"""

@cli.group(name="math")
def math_grp():
    """Math engine commands"""

@cli.group()
def company():
    """Company builder commands"""

@cli.group(name="eval")
def eval_grp():
    """Evaluation commands"""

@cli.group()
def replay():
    """Audit replay commands"""

@cli.group()
def policy():
    """Policy management"""

@cli.group()
def checkpoint():
    """Checkpoint management"""

@cli.group()
def workflow():
    """Workflow engine commands"""

@cli.group(name="config")
def config_grp():
    """Configuration management"""

@cli.group()
def plugin():
    """Plugin management"""

@cli.group()
def security():
    """Security commands"""


# Register subcommand modules
def _register_all():
    from astra_cli.commands import mission as m_mod
    from astra_cli.commands import tool as t_mod
    from astra_cli.commands import agent as a_mod
    from astra_cli.commands import memory as mem_mod
    from astra_cli.commands import verify as v_mod
    from astra_cli.commands import approval as ap_mod
    from astra_cli.commands import sandbox as sb_mod
    from astra_cli.commands import science as sc_mod
    from astra_cli.commands import math as math_mod
    from astra_cli.commands import company as co_mod
    from astra_cli.commands import eval as ev_mod
    from astra_cli.commands import replay as rp_mod
    from astra_cli.commands import policy as po_mod
    from astra_cli.commands import checkpoint as cp_mod
    from astra_cli.commands import workflow as wf_mod
    from astra_cli.commands import config as cfg_mod
    from astra_cli.commands import plugin as pl_mod
    from astra_cli.commands import security as sec_mod

    m_mod.register(mission)
    t_mod.register(tool)
    a_mod.register(agent)
    mem_mod.register(memory)
    v_mod.register(verify)
    ap_mod.register(approval)
    sb_mod.register(sandbox)
    sc_mod.register(science)
    math_mod.register(math_grp)
    co_mod.register(company)
    ev_mod.register(eval_grp)
    rp_mod.register(replay)
    po_mod.register(policy)
    cp_mod.register(checkpoint)
    wf_mod.register(workflow)
    cfg_mod.register(config_grp)
    pl_mod.register(plugin)
    sec_mod.register(security)


_register_all()
