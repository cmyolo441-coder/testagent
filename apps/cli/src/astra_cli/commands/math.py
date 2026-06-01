"""Math Commands — conjectures, proof sketching, counter-examples."""
import click
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading, json_out
from math_engine.conjecture_generator import ConjectureGenerator
from math_engine.proof_planner import ProofPlanner
from math_engine.counterexample_finder import CounterexampleFinder


def register(group):
    @group.command("conjecture")
    @click.argument("subject")
    @click.option("--n", default=3, type=int)
    @click.pass_context
    def conjecture(ctx, subject, n):
        for c in ConjectureGenerator().generate(subject, n=n):
            click.echo(f"C{c['id']}: {c['statement']}  (novelty={c['novelty']:.2f})")

    @group.command("prove")
    @click.argument("statement")
    @click.pass_context
    def prove(ctx, statement):
        plan = ProofPlanner().plan(statement)
        json_out(plan, title="Proof Plan")

    @group.command("counter")
    @click.argument("statement")
    @click.option("--budget", default=100, type=int)
    @click.pass_context
    def counter(ctx, statement, budget):
        out = CounterexampleFinder().search(statement, budget=budget)
        json_out(out, title="Counterexample Search")
