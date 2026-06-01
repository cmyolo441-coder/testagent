"""Company Commands — startup planning and build orchestration."""
import click
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading, json_out
from company_builder_engine import (
    StartupStrategy, MarketResearch, ProductManager, LaunchOrchestrator, GrowthLoop,
)


def register(group):
    @group.command("plan")
    @click.argument("idea")
    @click.option("--months", default=6, type=int)
    @click.pass_context
    def plan(ctx, idea, months):
        strat = StartupStrategy().build(idea, months=months)
        json_out(strat, title=f"Startup plan: {idea}")

    @group.command("market")
    @click.argument("idea")
    @click.pass_context
    def market(ctx, idea):
        json_out(MarketResearch().research(idea), title="Market Research")

    @group.command("product")
    @click.argument("idea")
    @click.pass_context
    def product(ctx, idea):
        json_out(ProductManager().spec(idea), title="Product Spec")

    @group.command("launch")
    @click.argument("product")
    @click.pass_context
    def launch(ctx, product):
        json_out(LaunchOrchestrator().checklist(product), title="Launch Checklist")

    @group.command("growth")
    @click.argument("product")
    @click.pass_context
    def growth(ctx, product):
        json_out(GrowthLoop().loops(product), title="Growth Loops")
