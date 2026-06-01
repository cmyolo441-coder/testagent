"""Science Commands — hypothesis, experiment, peer-review workflows."""
import click
import json
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading, json_out
from science_engine.hypothesis_generator import HypothesisGenerator
from science_engine.experiment_planner import ExperimentPlanner
from science_engine.falsification_engine import FalsificationEngine
from science_engine.peer_review_orchestrator import PeerReviewOrchestrator


def register(group):
    @group.command("hypothesis")
    @click.argument("topic")
    @click.option("--n", default=3, type=int, help="Number of hypotheses")
    @click.pass_context
    def hypothesis(ctx, topic, n):
        gen = HypothesisGenerator()
        hs = gen.generate(topic, n=n)
        heading(f"Hypotheses on: {topic}")
        for h in hs:
            click.echo(f"H{h['id']}: {h['statement']}")
            click.echo(f"   testable: {h['testable']}  novelty: {h['novelty']:.2f}")

    @group.command("experiment")
    @click.argument("hypothesis_text")
    @click.pass_context
    def experiment(ctx, hypothesis_text):
        plan = ExperimentPlanner().plan(hypothesis_text)
        json_out(plan, title="Experiment Plan")

    @group.command("falsify")
    @click.argument("claim")
    @click.pass_context
    def falsify(ctx, claim):
        attacks = FalsificationEngine().attack(claim)
        heading(f"Falsification attempts for: {claim}")
        for a in attacks:
            click.echo(f"- {a['attack']} (severity={a['severity']})")

    @group.command("review")
    @click.argument("text")
    @click.option("--reviewers", default=3, type=int)
    @click.pass_context
    def review(ctx, text, reviewers):
        out = PeerReviewOrchestrator().run(text, reviewer_count=reviewers)
        json_out(out, title="Peer Review")
