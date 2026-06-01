"""Checkpoint Commands — list, restore mission checkpoints."""
import click
import json
from sqlalchemy import create_engine, text
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading, json_out


def register(group):
    @group.command("list")
    @click.argument("mission_id")
    @click.pass_context
    def list_cmd(ctx, mission_id):
        astra = ctx.obj
        eng = create_engine(f"sqlite:///{astra.db_path}")
        with eng.connect() as conn:
            rows = conn.execute(text("SELECT id, note, created_at FROM checkpoints WHERE mission_id=:m ORDER BY created_at DESC"),
                                {"m": mission_id}).fetchall()
        if not rows:
            info("No checkpoints."); return
        for r in rows:
            click.echo(f"{r[0]}  {r[2]}  — {r[1]}")

    @group.command("restore")
    @click.argument("checkpoint_id")
    @click.pass_context
    def restore(ctx, checkpoint_id):
        astra = ctx.obj
        eng = create_engine(f"sqlite:///{astra.db_path}")
        with eng.connect() as conn:
            row = conn.execute(text("SELECT mission_id, snapshot_json FROM checkpoints WHERE id=:id"),
                               {"id": checkpoint_id}).first()
            if not row:
                error(f"Not found: {checkpoint_id}"); return
            mission_id, snap = row[0], json.loads(row[1])
            for tid, status in snap.items():
                conn.execute(text("UPDATE tasks SET status=:s WHERE id=:id"), {"s": status, "id": tid})
            conn.commit()
        success(f"Restored {len(snap)} task statuses from {checkpoint_id} (mission {mission_id})")
