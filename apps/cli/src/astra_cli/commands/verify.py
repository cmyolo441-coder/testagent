"""Verify Commands — extract and verify claims, produce verification reports."""
import click
import json
from astra_cli.context import AstraContext
from astra_cli.output import success, error, info, heading, json_out
from truth_engine.claim_extractor import ClaimExtractor
from truth_engine.verification_reporter import VerificationReporter


def register(group):
    @group.command("claims")
    @click.argument("text", required=False)
    @click.option("--file", "file_path", default=None, type=click.Path(exists=True))
    @click.pass_context
    def claims(ctx, text, file_path):
        """Extract checkable claims from text or a file."""
        if file_path:
            text = open(file_path).read()
        if not text:
            error("Provide TEXT or --file"); return
        ex = ClaimExtractor()
        cs = ex.extract_claims(text)
        info(f"Extracted {len(cs)} claims")
        for c in cs[:50]:
            click.echo(f"[{c.claim_type.value}] conf={c.confidence.value} neg={c.negated} → {c.text[:100]}")
        json_out(ex.get_claim_summary(cs), title="Summary")

    @group.command("report")
    @click.argument("text", required=False)
    @click.option("--file", "file_path", default=None, type=click.Path(exists=True))
    @click.option("--level", default=2, type=click.IntRange(0, 5), help="Target verification level (0-5)")
    @click.pass_context
    def report(ctx, text, file_path, level):
        """Produce a verification report for the given text."""
        if file_path:
            text = open(file_path).read()
        if not text:
            error("Provide TEXT or --file"); return
        ex = ClaimExtractor()
        cs = ex.extract_claims(text)
        rep = VerificationReporter()
        out = rep.generate_report(cs, target_level=level)
        json_out(out, title=f"Verification Report (level-{level})")

    @group.command("claim")
    @click.argument("claim_id")
    @click.pass_context
    def claim(ctx, claim_id):
        """Show stored claim by ID from local memory store."""
        try:
            from memory_engine.stores.sqlite_store import SQLiteMemoryStore
        except Exception as e:
            error(f"memory_engine unavailable: {e}")
            return

        actx: AstraContext = ctx.obj if ctx.obj is not None else AstraContext()
        db_path = actx.workspace / "astra.sqlite3"
        if not db_path.exists():
            # Fall back to standard local-first .astra directory path.
            alt = actx.astra_dir / "astra.sqlite3"
            if alt.exists():
                db_path = alt
            else:
                error(f"No memory store found at {db_path}")
                return

        try:
            store = SQLiteMemoryStore(db_path)
        except Exception as e:
            error(f"Failed to open memory store at {db_path}: {e}")
            return

        record = None
        try:
            record = store.retrieve(claim_id)
        except Exception as e:
            error(f"retrieve() failed: {e}")
            return

        if record is None:
            # Fall back: search recent memories tagged 'claim' with metadata['claim_id'] == claim_id.
            try:
                candidates = store.search(tags=["claim"], limit=200)
            except Exception as e:
                error(f"search() failed: {e}")
                return
            matches = [r for r in candidates if (r.metadata or {}).get("claim_id") == claim_id]
            if not matches:
                error(f"Claim not found: {claim_id}")
                return
            record = matches[0]
            info(f"Found {len(matches)} memory record(s) tagged 'claim' matching {claim_id}; showing most-important.")

        try:
            store.update_access(record.id)
        except Exception:
            pass

        payload = record.to_dict()
        json_out(payload, title=f"Claim {claim_id}")

        # Re-extract claim metadata via ClaimExtractor on stored content.
        content = (record.content or "").strip()
        if content:
            try:
                ex = ClaimExtractor()
                cs = ex.extract_claims(content)
                heading(f"Re-extracted claims ({len(cs)})")
                for c in cs[:10]:
                    click.echo(
                        f"[{c.claim_type.value}] conf={c.confidence.value} neg={c.negated} → {c.text[:100]}"
                    )
                json_out(ex.get_claim_summary(cs), title="Extraction Summary")
            except Exception as e:
                error(f"Re-extraction failed: {e}")

        # Display verification level if available in metadata.
        vlevel = (record.metadata or {}).get("verification_level")
        if vlevel is not None:
            success(f"verification_level = {vlevel}")
        else:
            info("No verification_level recorded in metadata.")
