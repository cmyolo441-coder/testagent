"""ASTRA CLI Output — Rich terminal formatting"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text
from rich import box
from typing import Any, Optional
import json

console = Console()
err_console = Console(stderr=True)


def success(msg: str):
    console.print(f"[green]✓[/green] {msg}")


def error(msg: str):
    err_console.print(f"[red]✗[/red] {msg}")


def info(msg: str):
    console.print(f"[blue]ℹ[/blue] {msg}")


def warning(msg: str):
    console.print(f"[yellow]⚠[/yellow] {msg}")


def heading(msg: str):
    console.print(Panel(msg, style="bold cyan", box=box.DOUBLE))


def json_out(data: Any, title: Optional[str] = None):
    formatted = json.dumps(data, indent=2, default=str)
    if title:
        console.print(Panel(formatted, title=title, box=box.ROUNDED))
    else:
        console.print(formatted)


def mission_table(missions: list[dict]):
    table = Table(title="Missions", box=box.ROUNDED, show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Goal", style="white")
    table.add_column("Horizon", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Progress", style="blue")
    for m in missions:
        table.add_row(
            m.get("id", "?"),
            m.get("goal", "?"),
            m.get("horizon", "?"),
            m.get("status", "created"),
            f"{m.get('progress', 0):.0f}%",
        )
    console.print(table)


def task_table(tasks: list[dict]):
    table = Table(title="Tasks", box=box.ROUNDED, show_lines=True)
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Status", style="yellow")
    table.add_column("Priority", style="magenta")
    table.add_column("Risk", style="red")
    for t in tasks:
        table.add_row(
            t.get("id", "?"),
            t.get("title", "?"),
            t.get("status", "pending"),
            t.get("priority", "medium"),
            t.get("risk_level", "low"),
        )
    console.print(table)


def dashboard_panel(sections: dict[str, Any]):
    for title, content in sections.items():
        console.print(Panel(str(content), title=title, box=box.ROUNDED))
