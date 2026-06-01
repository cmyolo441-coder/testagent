"""Memory Commands — store/search/show/forget durable memories."""
import click
import json
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading, json_out
from memory_engine.stores.sqlite_store import SQLiteMemoryStore, MemoryRecord


def _store(ctx: AstraContext) -> SQLiteMemoryStore:
    return SQLiteMemoryStore(ctx.astra_dir / "memory" / "memory.sqlite3")


def register(group):
    @group.command("store")
    @click.argument("content")
    @click.option("--type", "memory_type", default="episodic",
                  type=click.Choice(["episodic", "semantic", "procedural", "working", "decision", "failure", "lessons"]))
    @click.option("--mission", default=None)
    @click.option("--tags", default="", help="Comma-separated tags")
    @click.option("--importance", default=0.5, type=float)
    @click.pass_context
    def store(ctx, content, memory_type, mission, tags, importance):
        s = _store(ctx.obj)
        rec = MemoryRecord(
            memory_type=memory_type, content=content, mission_id=mission,
            tags=[t.strip() for t in tags.split(",") if t.strip()],
            importance=importance,
        )
        mid = s.store(rec)
        success(f"Memory stored: {mid}")

    @group.command("search")
    @click.argument("query", required=False, default=None)
    @click.option("--type", "memory_type", default=None)
    @click.option("--mission", default=None)
    @click.option("--limit", default=20, type=int)
    @click.option("--min-importance", default=0.0, type=float)
    @click.pass_context
    def search(ctx, query, memory_type, mission, limit, min_importance):
        s = _store(ctx.obj)
        results = s.search(query=query, memory_type=memory_type, mission_id=mission,
                           limit=limit, min_importance=min_importance)
        if not results:
            info("No memories."); return
        for r in results:
            click.echo(f"[{r.memory_type}] {r.id}  imp={r.importance:.2f}  {r.content[:80]}")

    @group.command("show")
    @click.argument("memory_id")
    @click.pass_context
    def show(ctx, memory_id):
        s = _store(ctx.obj)
        rec = s.retrieve(memory_id)
        if not rec:
            error(f"Not found: {memory_id}"); return
        s.update_access(memory_id)
        json_out(rec.to_dict(), title=f"Memory {memory_id}")

    @group.command("forget")
    @click.argument("memory_id")
    @click.confirmation_option(prompt="Really forget this memory?")
    @click.pass_context
    def forget(ctx, memory_id):
        s = _store(ctx.obj)
        if s.delete(memory_id):
            success(f"Forgotten: {memory_id}")
        else:
            error(f"Not found: {memory_id}")

    @group.command("link")
    @click.argument("source_id")
    @click.argument("target_id")
    @click.option("--relation", default="related")
    @click.option("--weight", default=1.0, type=float)
    @click.pass_context
    def link(ctx, source_id, target_id, relation, weight):
        s = _store(ctx.obj)
        s.add_edge(source_id, target_id, relation, weight)
        success(f"Linked: {source_id} --[{relation}]--> {target_id}")

    @group.command("stats")
    @click.pass_context
    def stats(ctx):
        s = _store(ctx.obj)
        json_out(s.get_stats(), title="Memory Stats")
