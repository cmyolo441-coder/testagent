"""Eval Commands — run evaluation suites and produce reports."""
import click
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading, json_out


def register(group):
    @group.command("run")
    @click.argument("suite",
                    type=click.Choice(["coding", "terminal", "security", "long-horizon",
                                       "science", "math", "agentic", "company-builder", "all"]))
    @click.option("--limit", default=None, type=int)
    @click.pass_context
    def run_suite(ctx, suite, limit):
        from evaluation_engine.runner import EvalRunner
        runner = EvalRunner()
        report = runner.run(suite, limit=limit)
        json_out(report, title=f"Eval: {suite}")

    @group.command("list")
    @click.pass_context
    def list_suites(ctx):
        from evaluation_engine.runner import EvalRunner
        for s in EvalRunner().available_suites():
            click.echo(f"  - {s}")

    @group.command("report")
    @click.argument("run_id")
    @click.pass_context
    def show_report(ctx, run_id):
        from evaluation_engine.runner import EvalRunner
        json_out(EvalRunner().fetch(run_id), title=f"Run {run_id}")
