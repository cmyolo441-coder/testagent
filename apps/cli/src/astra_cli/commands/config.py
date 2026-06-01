"""Config Commands — get, set, show astra configuration."""
import click
import json
from astra_cli.context import AstraContext
from astra_cli.config import AstraConfig
from astra_cli.output import success, error, info, heading, json_out


def register(group):
    @group.command("show")
    @click.pass_context
    def show(ctx):
        cfg = AstraConfig.load(ctx.obj.config_path)
        json_out(cfg.to_dict(), title=f"Config @ {ctx.obj.config_path}")

    @group.command("get")
    @click.argument("key")
    @click.pass_context
    def get(ctx, key):
        cfg = AstraConfig.load(ctx.obj.config_path)
        v = cfg.get(key)
        if v is None: error(f"Unset: {key}")
        else: click.echo(json.dumps(v, indent=2, default=str))

    @group.command("set")
    @click.argument("key")
    @click.argument("value")
    @click.pass_context
    def set_cmd(ctx, key, value):
        cfg = AstraConfig.load(ctx.obj.config_path)
        # Try JSON parse, fall back to literal string
        try: parsed = json.loads(value)
        except Exception: parsed = value
        cfg.set(key, parsed)
        cfg.save()
        success(f"{key} = {parsed}")

    @group.command("reset")
    @click.confirmation_option(prompt="Reset config to defaults?")
    @click.pass_context
    def reset(ctx):
        from astra_cli.config import DEFAULT_CONFIG
        cfg = AstraConfig(path=ctx.obj.config_path, data=dict(DEFAULT_CONFIG))
        cfg.save()
        success("Config reset to defaults.")
