"""Dashboard — Mission Control Display"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.columns import Columns
from astra_cli.context import AstraContext
from astra_cli.output import heading, info, error

console = Console()


def show_dashboard(ctx: AstraContext):
    """Display the ASTRA Command dashboard"""
    from sqlalchemy import create_engine, text

    engine = create_engine(f"sqlite:///{ctx.db_path}")

    heading("ASTRA COMMAND — Mission Control Dashboard")

    try:
        with engine.connect() as conn:
            # Mission summary
            missions = conn.execute(text("SELECT COUNT(*) FROM missions")).scalar()
            active = conn.execute(text("SELECT COUNT(*) FROM missions WHERE status != 'completed'")).scalar()
            completed = conn.execute(text("SELECT COUNT(*) FROM missions WHERE status = 'completed'")).scalar()

            # Task summary
            total_tasks = conn.execute(text("SELECT COUNT(*) FROM tasks")).scalar()
            done_tasks = conn.execute(text("SELECT COUNT(*) FROM tasks WHERE status = 'done'")).scalar()
            pending_tasks = conn.execute(text("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")).scalar()
            failed_tasks = conn.execute(text("SELECT COUNT(*) FROM tasks WHERE status = 'failed'")).scalar()

            # Checkpoints
            checkpoints = conn.execute(text("SELECT COUNT(*) FROM checkpoints")).scalar()

            # Audit events
            audit_count = conn.execute(text("SELECT COUNT(*) FROM audit_events")).scalar()

            # Mission list
            mission_rows = conn.execute(text("SELECT id, goal, horizon, status, progress FROM missions ORDER BY created_at DESC LIMIT 5"))
            recent_missions = [dict(row._mapping) for row in mission_rows]

    except Exception:
        info("No data yet. Create a mission to get started!")
        info("  astra mission create 'your goal here'")
        return

    # Summary panel
    summary = Table(show_header=False, box=None)
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", style="white", justify="right")
    summary.add_row("Total Missions", str(missions))
    summary.add_row("Active", str(active))
    summary.add_row("Completed", str(completed))
    summary.add_row("Total Tasks", str(total_tasks))
    summary.add_row("Tasks Done", f"[green]{done_tasks}[/green]")
    summary.add_row("Tasks Pending", f"[yellow]{pending_tasks}[/yellow]")
    summary.add_row("Tasks Failed", f"[red]{failed_tasks}[/red]")
    summary.add_row("Checkpoints", str(checkpoints))
    summary.add_row("Audit Events", str(audit_count))

    console.print(Panel(summary, title="[bold cyan]System Overview[/bold cyan]", border_style="cyan"))

    # Recent missions
    if recent_missions:
        table = Table(title="Recent Missions", show_lines=True)
        table.add_column("ID", style="cyan")
        table.add_column("Goal", style="white")
        table.add_column("Horizon", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Progress", style="blue")
        for m in recent_missions:
            table.add_row(
                m["id"],
                m["goal"][:50] + ("..." if len(m["goal"]) > 50 else ""),
                m["horizon"],
                m["status"],
                f"{m['progress']:.0f}%",
            )
        console.print(table)

    # Status bar
    console.print()
    info("Commands: astra mission create/list/show/tasks | astra dashboard | astra tool shell")
