"""Replay Commands — replay audit logs for forensic timeline."""
import click
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading, json_out
from sqlalchemy import create_engine, text


def register(group):
    @group.command("mission")
    @click.argument("mission_id")
    @click.option("--limit", default=200, type=int)
    @click.pass_context
    def replay_mission(ctx, mission_id, limit):
        astra = ctx.obj
        eng = create_engine(f"sqlite:///{astra.db_path}")
        with eng.connect() as conn:
            rows = conn.execute(text(
                "SELECT id, event_type, entity_type, entity_id, timestamp, details FROM audit_events "
                "WHERE entity_id=:m OR details LIKE :pat ORDER BY timestamp ASC LIMIT :lim"
            ), {"m": mission_id, "pat": f"%{mission_id}%", "lim": limit}).fetchall()
        if not rows:
            info("No events."); return
        heading(f"Replay: {mission_id} — {len(rows)} events")
        for r in rows:
            click.echo(f"{r[4]}  {r[1]:<24} {r[2]}/{r[3]}")

    @group.command("verify-chain")
    @click.pass_context
    def verify_chain(ctx):
        """Verify the audit log hash chain."""
        from safety_engine.audit.merkle_chain import MerkleChain
        astra = ctx.obj
        eng = create_engine(f"sqlite:///{astra.db_path}")
        with eng.connect() as conn:
            rows = conn.execute(text("SELECT id, event_type, details, prev_hash, event_hash FROM audit_events ORDER BY id")).fetchall()
        ok, broken = MerkleChain.verify_rows(rows)
        if ok: success(f"Audit chain verified across {len(rows)} events")
        else:  error(f"BROKEN at event id={broken}")
