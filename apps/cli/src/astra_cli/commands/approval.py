"""Approval Commands — list, approve, reject pending risky actions."""
import click
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading, json_out
from safety_engine.approvals.approval_store import ApprovalStore


def _store(ctx: AstraContext) -> ApprovalStore:
    return ApprovalStore(db_path=str(ctx.astra_dir / "approvals.sqlite3"))


def register(group):
    @group.command("list")
    @click.option("--status", default="pending", type=click.Choice(["pending", "approved", "rejected", "expired", "all"]))
    @click.pass_context
    def list_cmd(ctx, status):
        s = _store(ctx.obj)
        reqs = s.list_requests(status=None if status == "all" else status)
        if not reqs:
            info(f"No approvals ({status})."); return
        for r in reqs:
            click.echo(f"{r.id}  [{r.status.value}]  risk={r.risk_score:>3}  type={r.action_type:<20} desc={r.description[:60]}")

    @group.command("approve")
    @click.argument("approval_id")
    @click.option("--by", default="user")
    @click.option("--note", default="")
    @click.pass_context
    def approve(ctx, approval_id, by, note):
        s = _store(ctx.obj)
        ok = s.approve(approval_id, approved_by=by, note=note)
        if ok: success(f"Approved: {approval_id}")
        else:  error(f"Not found: {approval_id}")

    @group.command("reject")
    @click.argument("approval_id")
    @click.option("--by", default="user")
    @click.option("--reason", default="")
    @click.pass_context
    def reject(ctx, approval_id, by, reason):
        s = _store(ctx.obj)
        ok = s.reject(approval_id, rejected_by=by, reason=reason)
        if ok: success(f"Rejected: {approval_id}")
        else:  error(f"Not found: {approval_id}")

    @group.command("show")
    @click.argument("approval_id")
    @click.pass_context
    def show(ctx, approval_id):
        s = _store(ctx.obj)
        r = s.get(approval_id)
        if not r: error(f"Not found: {approval_id}"); return
        json_out(r.to_dict(), title=f"Approval {approval_id}")
