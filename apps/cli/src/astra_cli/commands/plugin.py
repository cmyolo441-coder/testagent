"""Plugin Commands — list, install, enable, disable plugins."""
import click
import json
from pathlib import Path
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading, json_out


def _registry_path(ctx: AstraContext) -> Path:
    return ctx.astra_dir / "plugins.json"


def _load(ctx: AstraContext) -> dict:
    p = _registry_path(ctx)
    if not p.exists():
        return {"plugins": {}}
    return json.loads(p.read_text())


def _save(ctx: AstraContext, data: dict):
    _registry_path(ctx).write_text(json.dumps(data, indent=2))


def register(group):
    @group.command("list")
    @click.pass_context
    def list_cmd(ctx):
        data = _load(ctx.obj)
        if not data["plugins"]:
            info("No plugins installed."); return
        for name, p in data["plugins"].items():
            status = "[enabled]" if p.get("enabled") else "[disabled]"
            click.echo(f"  {status:<11} {name:<24} v{p.get('version','?')} — {p.get('description','')}")

    @group.command("install")
    @click.argument("name")
    @click.option("--version", default="0.0.1")
    @click.option("--description", default="")
    @click.pass_context
    def install(ctx, name, version, description):
        data = _load(ctx.obj)
        data["plugins"][name] = {"enabled": True, "version": version, "description": description}
        _save(ctx.obj, data)
        success(f"Installed: {name} v{version}")

    @group.command("enable")
    @click.argument("name")
    @click.pass_context
    def enable(ctx, name):
        data = _load(ctx.obj)
        if name not in data["plugins"]:
            error(f"Not installed: {name}"); return
        data["plugins"][name]["enabled"] = True
        _save(ctx.obj, data); success(f"Enabled: {name}")

    @group.command("disable")
    @click.argument("name")
    @click.pass_context
    def disable(ctx, name):
        data = _load(ctx.obj)
        if name not in data["plugins"]:
            error(f"Not installed: {name}"); return
        data["plugins"][name]["enabled"] = False
        _save(ctx.obj, data); success(f"Disabled: {name}")

    @group.command("remove")
    @click.argument("name")
    @click.pass_context
    def remove(ctx, name):
        data = _load(ctx.obj)
        if name in data["plugins"]:
            del data["plugins"][name]; _save(ctx.obj, data); success(f"Removed: {name}")
        else:
            error(f"Not installed: {name}")
