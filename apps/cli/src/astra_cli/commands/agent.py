"""Agent Commands — run/step/list/show agents tied to missions."""
import click
import json
import uuid
from datetime import datetime, timezone
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading, json_out
from sqlalchemy import create_engine, text


def _engine(ctx: AstraContext):
    eng = create_engine(f"sqlite:///{ctx.db_path}")
    with eng.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                mission_id TEXT,
                role TEXT NOT NULL,
                status TEXT DEFAULT 'idle',
                model TEXT,
                iterations INTEGER DEFAULT 0,
                last_step_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS agent_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                iteration INTEGER NOT NULL,
                phase TEXT,
                observation TEXT,
                thought TEXT,
                action_json TEXT,
                result_json TEXT,
                verification TEXT,
                timestamp TEXT NOT NULL
            )
        """))
        conn.commit()
    return eng


def register(group):
    @group.command("spawn")
    @click.argument("mission_id")
    @click.option("--role", "-r", default="executor", help="Agent role")
    @click.option("--model", "-m", default="claude-opus-4-8")
    @click.pass_context
    def spawn(ctx, mission_id, role, model):
        """Spawn an agent for a mission."""
        astra = ctx.obj
        eng = _engine(astra)
        aid = f"A-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        with eng.connect() as conn:
            conn.execute(text(
                "INSERT INTO agents (id, mission_id, role, status, model, created_at, updated_at) "
                "VALUES (:id, :m, :r, 'idle', :model, :now, :now)"
            ), {"id": aid, "m": mission_id, "r": role, "model": model, "now": now})
            conn.commit()
        success(f"Agent spawned: {aid} (role={role})")

    @group.command("list")
    @click.option("--mission", default=None)
    @click.pass_context
    def list_agents(ctx, mission):
        astra = ctx.obj
        eng = _engine(astra)
        with eng.connect() as conn:
            if mission:
                rows = conn.execute(text("SELECT id, role, status, iterations, model FROM agents WHERE mission_id=:m"), {"m": mission}).fetchall()
            else:
                rows = conn.execute(text("SELECT id, role, status, iterations, model FROM agents ORDER BY created_at DESC")).fetchall()
        if not rows:
            info("No agents."); return
        for r in rows:
            click.echo(f"{r[0]:>12}  role={r[1]:<14} status={r[2]:<10} iter={r[3]:<4} model={r[4]}")

    @group.command("step")
    @click.argument("agent_id")
    @click.option("--observation", "-o", default="(none)")
    @click.option("--thought", "-t", default="")
    @click.option("--action", "-a", default="{}")
    @click.pass_context
    def step(ctx, agent_id, observation, thought, action):
        """Record a single agent step (Observe/Think/Act/Verify)."""
        astra = ctx.obj
        eng = _engine(astra)
        now = datetime.now(timezone.utc).isoformat()
        with eng.connect() as conn:
            row = conn.execute(text("SELECT iterations FROM agents WHERE id=:id"), {"id": agent_id}).first()
            if not row:
                error(f"Agent not found: {agent_id}"); return
            it = (row[0] or 0) + 1
            conn.execute(text(
                "INSERT INTO agent_steps (agent_id, iteration, phase, observation, thought, action_json, timestamp) "
                "VALUES (:a, :i, 'act', :o, :t, :ax, :now)"
            ), {"a": agent_id, "i": it, "o": observation, "t": thought, "ax": action, "now": now})
            conn.execute(text("UPDATE agents SET iterations=:i, status='running', updated_at=:now WHERE id=:id"),
                         {"i": it, "now": now, "id": agent_id})
            conn.commit()
        success(f"Step {it} recorded for {agent_id}")

    @group.command("show")
    @click.argument("agent_id")
    @click.pass_context
    def show(ctx, agent_id):
        astra = ctx.obj
        eng = _engine(astra)
        with eng.connect() as conn:
            r = conn.execute(text("SELECT * FROM agents WHERE id=:id"), {"id": agent_id}).mappings().first()
            if not r:
                error(f"Not found: {agent_id}"); return
            heading(f"Agent {agent_id}")
            for k, v in r.items():
                info(f"{k}: {v}")
            steps = conn.execute(text("SELECT iteration, phase, observation, thought FROM agent_steps WHERE agent_id=:id ORDER BY iteration DESC LIMIT 10"),
                                 {"id": agent_id}).fetchall()
        if steps:
            heading("Recent steps")
            for s in steps:
                click.echo(f"  #{s[0]} [{s[1]}] obs={s[2][:40]}  thought={s[3][:40]}")

    @group.command("run")
    @click.argument("mission_id")
    @click.option("--max-iters", default=5, help="Max agent loop iterations (dry, no LLM)")
    @click.pass_context
    def run(ctx, mission_id, max_iters):
        """Run a basic agent loop over the mission's pending tasks (no LLM, deterministic)."""
        from agent_engine.core.agent_loop import AgentLoop, LoopPhase
        astra = ctx.obj
        eng = _engine(astra)
        with eng.connect() as conn:
            tasks = conn.execute(text("SELECT id, title, status FROM tasks WHERE mission_id=:m AND status='pending'"),
                                 {"m": mission_id}).fetchall()
        if not tasks:
            info("No pending tasks."); return
        heading(f"Running mission {mission_id} ({len(tasks)} tasks)")
        loop = AgentLoop(max_iterations=min(max_iters, len(tasks)))

        idx = {"i": 0}
        def observe(ctx_):
            if idx["i"] >= len(tasks): return "no more tasks"
            return f"Task: {tasks[idx['i']][1]}"
        def think(ctx_, obs):
            return f"Plan: complete '{obs}' via standard procedure"
        def act(ctx_, thought):
            task = tasks[idx["i"]]
            now = datetime.now(timezone.utc).isoformat()
            with eng.connect() as conn:
                conn.execute(text("UPDATE tasks SET status='done', completed_at=:now, updated_at=:now WHERE id=:id"),
                             {"now": now, "id": task[0]})
                conn.commit()
            idx["i"] += 1
            return {"task_id": task[0], "status": "done"}
        def verify(ctx_, result):
            return "ok" if result and result.get("status") == "done" else "fail"
        def stop(ctx_, step):
            return idx["i"] >= len(tasks)

        loop.set_observe(observe); loop.set_think(think); loop.set_act(act)
        loop.set_verify(verify); loop.set_stop(stop)
        steps = loop.run()
        success(f"Loop done: {len(steps)} iterations, {idx['i']} tasks completed")
