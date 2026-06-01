"""Workflow Commands — list, run, and inspect workflows."""
import click
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading, json_out


def register(group):
    @group.command("list")
    @click.pass_context
    def list_cmd(ctx):
        from workflow_engine import list_workflows
        wfs = list_workflows()
        if not wfs:
            info("No workflows registered."); return
        for w in wfs:
            click.echo(f"  {w['name']:<24} — {w['description']}")

    @group.command("run")
    @click.argument("name")
    @click.option("--input", "input_json", default="{}", help="JSON input")
    @click.pass_context
    def run(ctx, name, input_json):
        import json
        from workflow_engine import run_workflow
        payload = json.loads(input_json)
        result = run_workflow(name, payload)
        json_out(result, title=f"Workflow: {name}")

    @group.command("show")
    @click.argument("name")
    @click.pass_context
    def show(ctx, name):
        from workflow_engine import describe_workflow
        info_ = describe_workflow(name)
        if not info_:
            error(f"Unknown: {name}"); return
        json_out(info_, title=name)
