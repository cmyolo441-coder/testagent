"""Policy Commands — load, list, and check action policies."""
import click
import json
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading, json_out


def register(group):
    @group.command("list")
    @click.pass_context
    def list_cmd(ctx):
        from safety_engine.approvals.approval_policy import default_policy
        json_out(default_policy(), title="Active Policy")

    @group.command("check")
    @click.argument("action")
    @click.argument("target", required=False, default="")
    @click.pass_context
    def check(ctx, action, target):
        from safety_engine.risk.risk_model import RiskAssessor
        from safety_engine.approvals.approval_policy import policy_decision
        assessor = RiskAssessor()
        if action == "command":
            score = assessor.assess_command(target)
        elif action == "file_write":
            score = assessor.assess_file_write(target)
        elif action == "file_delete":
            score = assessor.assess_file_delete(target)
        else:
            score = 50
        decision = policy_decision(action, target, score)
        json_out({"action": action, "target": target, "risk": score, "decision": decision},
                 title="Policy Decision")
