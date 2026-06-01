"""Security Commands — secret scan, injection check, supply-chain audit."""
import click
from pathlib import Path
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading, json_out
from safety_engine.detection.secret_detector import SecretDetector


def register(group):
    @group.command("scan-secrets")
    @click.argument("path", default=".")
    @click.option("--ext", default=".py,.js,.ts,.env,.yaml,.yml,.json,.txt,.md")
    @click.pass_context
    def scan_secrets(ctx, path, ext):
        exts = set(e.strip() for e in ext.split(",") if e.strip())
        det = SecretDetector()
        hits = []
        for p in Path(path).rglob("*"):
            if p.is_file() and p.suffix in exts and p.stat().st_size < 1_000_000:
                try: text = p.read_text(errors="ignore")
                except Exception: continue
                for h in det.scan(text):
                    hits.append({"file": str(p), **h})
        if not hits:
            success("No secrets detected"); return
        info(f"{len(hits)} suspect secrets")
        for h in hits[:50]:
            click.echo(f"  [{h['kind']}] {h['file']}:{h['line']}  — {h['evidence'][:60]}")

    @group.command("check-injection")
    @click.argument("text")
    @click.pass_context
    def check_inj(ctx, text):
        from safety_engine.detection.prompt_injection_detector import PromptInjectionDetector
        res = PromptInjectionDetector().check(text)
        json_out(res, title="Prompt Injection Check")

    @group.command("audit-supply")
    @click.argument("requirements_file", type=click.Path(exists=True))
    @click.pass_context
    def audit_supply(ctx, requirements_file):
        from safety_engine.detection.supply_chain_detector import SupplyChainAuditor
        out = SupplyChainAuditor().audit(requirements_file)
        json_out(out, title="Supply-Chain Audit")
