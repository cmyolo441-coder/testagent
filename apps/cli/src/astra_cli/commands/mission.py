"""Mission Commands — create, list, show, tasks, update, checkpoint"""
import click
import uuid
import json
from datetime import datetime, timezone
from pathlib import Path
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading, mission_table, task_table, json_out
from planning_engine.mission_control.mission_contract import MissionContract
from planning_engine.mission_control.objective_tree import ObjectiveTree
from planning_engine.mission_control.milestone_planner import MilestonePlanner
from planning_engine.mission_control.progress_tracker import ProgressTracker
from safety_engine.risk.risk_model import RiskAssessor


def get_db(ctx: AstraContext):
    from sqlalchemy import create_engine, text
    engine = create_engine(f"sqlite:///{ctx.db_path}")
    _init_db(engine)
    return engine


def _init_db(engine):
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS missions (
                id TEXT PRIMARY KEY,
                goal TEXT NOT NULL,
                horizon TEXT DEFAULT '3m',
                agent_count INTEGER DEFAULT 1,
                verification_level INTEGER DEFAULT 2,
                status TEXT DEFAULT 'created',
                progress REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata_json TEXT DEFAULT '{}'
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                mission_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                risk_level TEXT DEFAULT 'low',
                assigned_agent TEXT,
                dependencies TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (mission_id) REFERENCES missions(id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id TEXT PRIMARY KEY,
                mission_id TEXT NOT NULL,
                note TEXT NOT NULL,
                snapshot_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (mission_id) REFERENCES missions(id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                actor TEXT DEFAULT 'cli',
                details TEXT DEFAULT '{}',
                timestamp TEXT NOT NULL,
                prev_hash TEXT,
                event_hash TEXT
            )
        """))
        conn.commit()


def register(cli_group):
    @cli_group.command("create")
    @click.argument("goal")
    @click.option("--horizon", "-h", default="3m", help="Mission horizon (e.g., 6m, 1y)")
    @click.option("--agents", "-a", default=1, help="Number of agents")
    @click.option("--verification", "-V", default="level-2", help="Verification level")
    @click.pass_context
    def create_mission(ctx, goal: str, horizon: str, agents: int, verification: str):
        """Create a new mission with objective tree and milestones"""
        astra_ctx = ctx.obj
        db = get_db(astra_ctx)

        mission_id = f"M-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()

        contract = MissionContract(
            id=mission_id,
            goal=goal,
            horizon=horizon,
            agent_count=agents,
            verification_level=verification,
        )

        tree = ObjectiveTree.from_goal(goal, mission_id)
        planner = MilestonePlanner(horizon)
        milestones = planner.generate_milestones(tree)

        from sqlalchemy import text
        with db.connect() as conn:
            conn.execute(
                text("INSERT INTO missions (id, goal, horizon, agent_count, verification_level, status, created_at, updated_at) VALUES (:id, :goal, :horizon, :agents, :vlevel, 'created', :now, :now)"),
                {"id": mission_id, "goal": goal, "horizon": horizon, "agents": agents, "vlevel": verification, "now": now},
            )
            for ms in milestones:
                conn.execute(
                    text("INSERT INTO tasks (id, mission_id, title, description, status, priority, risk_level, created_at, updated_at) VALUES (:id, :mid, :title, :desc, 'pending', :priority, :risk, :now, :now)"),
                    {"id": ms["id"], "mid": mission_id, "title": ms["title"], "desc": ms.get("description", ""), "priority": ms.get("priority", "medium"), "risk": ms.get("risk", "low"), "now": now},
                )
            conn.execute(
                text("INSERT INTO audit_events (event_type, entity_type, entity_id, details, timestamp) VALUES ('mission_created', 'mission', :eid, :details, :now)"),
                {"eid": mission_id, "details": json.dumps({"goal": goal, "horizon": horizon}), "now": now},
            )
            conn.commit()

        success(f"Mission created: {mission_id}")
        info(f"Goal: {goal}")
        info(f"Horizon: {horizon} | Agents: {agents} | Verification: {verification}")
        info(f"Milestones: {len(milestones)} tasks generated")

    @cli_group.command("list")
    @click.pass_context
    def list_missions(ctx):
        """List all missions"""
        astra_ctx = ctx.obj
        db = get_db(astra_ctx)
        from sqlalchemy import text
        with db.connect() as conn:
            result = conn.execute(text("SELECT id, goal, horizon, status, progress FROM missions ORDER BY created_at DESC"))
            rows = [dict(row._mapping) for row in result]
        if not rows:
            info("No missions found. Create one with: astra mission create 'your goal'")
            return
        mission_table(rows)

    @cli_group.command("show")
    @click.argument("mission_id")
    @click.pass_context
    def show_mission(ctx, mission_id: str):
        """Show mission details"""
        astra_ctx = ctx.obj
        db = get_db(astra_ctx)
        from sqlalchemy import text
        with db.connect() as conn:
            result = conn.execute(text("SELECT * FROM missions WHERE id = :id"), {"id": mission_id})
            row = result.mappings().first()
            if not row:
                error(f"Mission not found: {mission_id}")
                return
            heading(f"Mission: {row['id']}")
            info(f"Goal: {row['goal']}")
            info(f"Horizon: {row['horizon']}")
            info(f"Status: {row['status']}")
            info(f"Progress: {row['progress']:.0f}%")
            info(f"Verification: Level-{row['verification_level']}")
            info(f"Agents: {row['agent_count']}")
            info(f"Created: {row['created_at']}")

    @cli_group.command("tasks")
    @click.argument("mission_id")
    @click.pass_context
    def list_tasks(ctx, mission_id: str):
        """List tasks for a mission"""
        astra_ctx = ctx.obj
        db = get_db(astra_ctx)
        from sqlalchemy import text
        with db.connect() as conn:
            result = conn.execute(
                text("SELECT id, title, status, priority, risk_level FROM tasks WHERE mission_id = :mid ORDER BY created_at"),
                {"mid": mission_id},
            )
            rows = [dict(row._mapping) for row in result]
        if not rows:
            info(f"No tasks found for mission: {mission_id}")
            return
        task_table(rows)

    @cli_group.command("update-task")
    @click.argument("task_id")
    @click.argument("status")
    @click.pass_context
    def update_task(ctx, task_id: str, status: str):
        """Update task status (pending, running, done, failed)"""
        astra_ctx = ctx.obj
        db = get_db(astra_ctx)
        from sqlalchemy import text
        now = datetime.now(timezone.utc).isoformat()
        completed_at = now if status == "done" else None
        with db.connect() as conn:
            conn.execute(
                text("UPDATE tasks SET status = :status, updated_at = :now, completed_at = :completed WHERE id = :id"),
                {"status": status, "now": now, "completed": completed_at, "id": task_id},
            )
            conn.commit()
        success(f"Task {task_id} → {status}")

        # Update mission progress
        result = db.connect().execute(
            text("SELECT mission_id FROM tasks WHERE id = :id"), {"id": task_id}
        )
        row = result.first()
        if row:
            _update_mission_progress(db, row[0])

    @cli_group.command("checkpoint")
    @click.argument("mission_id")
    @click.argument("note")
    @click.pass_context
    def add_checkpoint(ctx, mission_id: str, note: str):
        """Add a checkpoint to a mission"""
        astra_ctx = ctx.obj
        db = get_db(astra_ctx)
        cp_id = f"CP-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        from sqlalchemy import text
        with db.connect() as conn:
            # Get current state
            tasks = conn.execute(
                text("SELECT id, status FROM tasks WHERE mission_id = :mid"), {"mid": mission_id}
            )
            snapshot = {row[0]: row[1] for row in tasks}

            conn.execute(
                text("INSERT INTO checkpoints (id, mission_id, note, snapshot_json, created_at) VALUES (:id, :mid, :note, :snap, :now)"),
                {"id": cp_id, "mid": mission_id, "note": note, "snap": json.dumps(snapshot), "now": now},
            )
            conn.execute(
                text("INSERT INTO audit_events (event_type, entity_type, entity_id, details, timestamp) VALUES ('checkpoint', 'mission', :eid, :details, :now)"),
                {"eid": mission_id, "details": json.dumps({"checkpoint_id": cp_id, "note": note}), "now": now},
            )
            conn.commit()
        success(f"Checkpoint added: {cp_id}")
        info(f"Note: {note}")


def _update_mission_progress(db, mission_id: str):
    from sqlalchemy import text
    with db.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM tasks WHERE mission_id = :mid"), {"mid": mission_id}).scalar()
        done = conn.execute(
            text("SELECT COUNT(*) FROM tasks WHERE mission_id = :mid AND status = 'done'"), {"mid": mission_id}
        ).scalar()
        progress = (done / total * 100) if total > 0 else 0
        conn.execute(
            text("UPDATE missions SET progress = :p, updated_at = :now WHERE id = :id"),
            {"p": progress, "now": datetime.now(timezone.utc).isoformat(), "id": mission_id},
        )
        conn.commit()
