#!/usr/bin/env python3
"""ASTRA Command OS — Unified Entry Point

A single, runnable entry point that bootstraps the monorepo sys.path and exposes
subcommands for self-testing, module discovery, an end-to-end demo, the CLI, the
TUI, and a doctor diagnostic. Designed to be runnable directly:

    python3 main.py self-test
    python3 main.py doctor
    python3 main.py modules
    python3 main.py demo
    python3 main.py cli ARGS...
    python3 main.py tui
"""
from __future__ import annotations

import argparse
import importlib
import os
import pkgutil
import platform
import sys
import traceback
from pathlib import Path

# ----------------------------------------------------------------------------
# sys.path bootstrap — must happen BEFORE any first-party import
# ----------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent

_SRC_DIRS = [
    _REPO_ROOT / "engines" / "planning-engine" / "src",
    _REPO_ROOT / "engines" / "truth-engine" / "src",
    _REPO_ROOT / "engines" / "memory-engine" / "src",
    _REPO_ROOT / "engines" / "safety-engine" / "src",
    _REPO_ROOT / "engines" / "agent-engine" / "src",
    _REPO_ROOT / "engines" / "identity-engine" / "src",
    _REPO_ROOT / "engines" / "collaboration-engine" / "src",
    _REPO_ROOT / "engines" / "science-engine" / "src",
    _REPO_ROOT / "engines" / "math-engine" / "src",
    _REPO_ROOT / "engines" / "company-builder-engine" / "src",
    _REPO_ROOT / "engines" / "code-intelligence-engine" / "src",
    _REPO_ROOT / "engines" / "workflow-engine" / "src",
    _REPO_ROOT / "engines" / "evaluation-engine" / "src",
    _REPO_ROOT / "engines" / "simulation-engine" / "src",
    _REPO_ROOT / "services" / "llm-gateway" / "src",
    _REPO_ROOT / "services" / "tool-executor" / "src",
    _REPO_ROOT / "services" / "sandbox-runner" / "src",
    _REPO_ROOT / "services" / "memory-service" / "src",
    _REPO_ROOT / "services" / "truth-service" / "src",
    _REPO_ROOT / "apps" / "cli" / "src",
    _REPO_ROOT / "apps" / "tui" / "src",
]


def _bootstrap_paths() -> list[str]:
    added: list[str] = []
    for p in _SRC_DIRS:
        sp = str(p)
        if p.exists() and sp not in sys.path:
            sys.path.insert(0, sp)
            added.append(sp)
    return added


_bootstrap_paths()


# ----------------------------------------------------------------------------
# Pretty printing — rich if available, plain print otherwise
# ----------------------------------------------------------------------------
try:
    from rich.console import Console  # type: ignore
    from rich.table import Table  # type: ignore
    from rich.panel import Panel  # type: ignore

    _console = Console()
    _HAS_RICH = True
except Exception:
    _console = None
    _HAS_RICH = False


def _print(msg: str = "") -> None:
    if _HAS_RICH and _console is not None:
        _console.print(msg)
    else:
        print(msg)


def _print_header(title: str) -> None:
    if _HAS_RICH and _console is not None:
        _console.print(Panel.fit(title, style="bold cyan"))
    else:
        bar = "=" * max(8, len(title) + 4)
        print(f"\n{bar}\n  {title}\n{bar}")


def _print_table(title: str, columns: list[str], rows: list[list[str]]) -> None:
    if _HAS_RICH and _console is not None:
        t = Table(title=title, show_lines=False)
        for c in columns:
            t.add_column(c, style="cyan", no_wrap=False)
        for r in rows:
            t.add_row(*[str(x) for x in r])
        _console.print(t)
    else:
        print(f"\n== {title} ==")
        header = " | ".join(columns)
        print(header)
        print("-" * len(header))
        for r in rows:
            print(" | ".join(str(x) for x in r))


# ----------------------------------------------------------------------------
# Package catalog — top-level packages we expect to import
# ----------------------------------------------------------------------------
TOP_PACKAGES = [
    "agent_engine",
    "planning_engine",
    "truth_engine",
    "memory_engine",
    "safety_engine",
    "identity_engine",
    "collaboration_engine",
    "science_engine",
    "math_engine",
    "company_builder_engine",
    "code_intelligence_engine",
    "workflow_engine",
    "evaluation_engine",
    "simulation_engine",
    "llm_gateway",
    "tool_executor",
    "sandbox_runner",
    "memory_service",
    "truth_service",
    "astra_cli",
    "astra_tui",
]


OPTIONAL_DEPS = [
    "click", "rich", "pydantic", "sqlalchemy", "aiosqlite", "httpx", "typer",
    "textual", "anthropic", "openai", "google.generativeai", "groq", "mistralai",
    "qdrant_client", "chromadb", "faiss", "redis", "psycopg2", "asyncpg",
    "boto3", "yaml", "numpy", "cryptography", "dateutil",
]


# ----------------------------------------------------------------------------
# Subcommand: self-test
# ----------------------------------------------------------------------------
def cmd_self_test(args: argparse.Namespace) -> int:
    _print_header("ASTRA self-test — importing every top-level package")
    results: list[list[str]] = []
    errors: list[str] = []
    failed = 0

    for pkg in TOP_PACKAGES:
        try:
            mod = importlib.import_module(pkg)
            path = getattr(mod, "__file__", "(namespace)") or "(namespace)"
            results.append([pkg, "OK", os.path.basename(path)])
        except Exception as e:
            failed += 1
            reason = f"{type(e).__name__}: {e}"
            errors.append(f"{pkg}: {reason}")
            results.append([pkg, "FAIL", reason[:60]])
            _print(f"[ERROR] {pkg}: {reason}")

    _print_table("Package Import Results", ["Package", "Status", "Detail"], results)

    # Quick sanity probes per package
    _print("")
    _print_header("Sanity probes")
    probes = [
        ("agent_engine.core.agent_runtime", "AgentRuntime"),
        ("identity_engine.identity_manifest", "IdentityManifest"),
        ("planning_engine.mission_control.mission_contract", "MissionContract"),
        ("planning_engine.mission_control.objective_tree", "ObjectiveTree"),
        ("planning_engine.mission_control.milestone_planner", "MilestonePlanner"),
        ("memory_engine.stores.sqlite_store", "SQLiteMemoryStore"),
        ("truth_engine.claim_extractor", "ClaimExtractor"),
        ("safety_engine.risk.risk_model", "RiskAssessor"),
        ("collaboration_engine.civilization_runtime.reputation_system", "ReputationSystem"),
        ("collaboration_engine.civilization_runtime.agent_society", "AgentSociety"),
        ("llm_gateway.governance.cost_tracker", "CostTracker"),
    ]
    probe_rows: list[list[str]] = []
    for modname, clsname in probes:
        try:
            mod = importlib.import_module(modname)
            cls = getattr(mod, clsname)
            probe_rows.append([modname, clsname, "OK"])
        except Exception as e:
            failed += 1
            reason = f"{type(e).__name__}: {e}"
            errors.append(f"{modname}.{clsname}: {reason}")
            probe_rows.append([modname, clsname, f"FAIL: {reason[:50]}"])
            _print(f"[ERROR] {modname}.{clsname}: {reason}")

    _print_table("Class probes", ["Module", "Class", "Status"], probe_rows)

    _print("")
    if failed == 0:
        _print("[OK] self-test passed — all packages importable, all probes succeeded.")
    else:
        _print(f"[WARN] self-test finished with {failed} failure(s).")

    # Stash errors for callers that want them
    cmd_self_test.last_errors = errors  # type: ignore[attr-defined]
    return 0 if failed == 0 else 1


# ----------------------------------------------------------------------------
# Subcommand: modules
# ----------------------------------------------------------------------------
def cmd_modules(args: argparse.Namespace) -> int:
    _print_header("Discovered packages and submodules")
    rows: list[list[str]] = []
    for pkg in TOP_PACKAGES:
        try:
            mod = importlib.import_module(pkg)
        except Exception as e:
            rows.append([pkg, "-", f"[ERROR] {type(e).__name__}: {e}"])
            continue
        if not hasattr(mod, "__path__"):
            rows.append([pkg, "(single-module)", ""])
            continue
        subs: list[str] = []
        try:
            for m in pkgutil.walk_packages(mod.__path__, prefix=pkg + "."):
                subs.append(m.name)
        except Exception as e:
            rows.append([pkg, "?", f"walk error: {e}"])
            continue
        rows.append([pkg, str(len(subs)), ", ".join(subs[:3]) + (" ..." if len(subs) > 3 else "")])
    _print_table("Modules", ["Package", "# submodules", "Sample"], rows)
    return 0


# ----------------------------------------------------------------------------
# Subcommand: demo
# ----------------------------------------------------------------------------
def cmd_demo(args: argparse.Namespace) -> int:
    _print_header("ASTRA end-to-end demo — wiring real engines together")
    summary: list[list[str]] = []

    # 1) AgentRuntime
    try:
        from agent_engine.core.agent_runtime import AgentRuntime, AgentConfig
        runtime = AgentRuntime(AgentConfig(name="DemoAgent", role="demo"))
        summary.append(["AgentRuntime", "ok", f"agent_id={runtime.config.agent_id}"])
    except Exception as e:
        summary.append(["AgentRuntime", "ERR", f"{type(e).__name__}: {e}"])
        runtime = None

    # 2) IdentityManifest
    try:
        from identity_engine.identity_manifest import IdentityManifest
        identity = IdentityManifest(
            name="DemoAgent",
            mission_statement="Operate the ASTRA demo safely.",
            core_values=["truthfulness", "safety"],
            allowed_actions=["read_file", "summarize"],
            forbidden_actions=["rm -rf /"],
        )
        summary.append(["IdentityManifest", "ok", identity.id])
    except Exception as e:
        summary.append(["IdentityManifest", "ERR", f"{type(e).__name__}: {e}"])
        identity = None

    # 3) MissionContract + ObjectiveTree + MilestonePlanner
    try:
        from planning_engine.mission_control.mission_contract import MissionContract
        from planning_engine.mission_control.objective_tree import ObjectiveTree
        from planning_engine.mission_control.milestone_planner import MilestonePlanner

        contract = MissionContract(id="MISSION-DEMO-001", goal="Build a small SaaS company", horizon="3m")
        tree = ObjectiveTree.from_goal(contract.goal, contract.id)
        planner = MilestonePlanner(horizon=contract.horizon)
        milestones = planner.generate_milestones(tree)
        summary.append([
            "Planning",
            "ok",
            f"objectives={len(tree.objectives)} milestones={len(milestones)}",
        ])
    except Exception as e:
        summary.append(["Planning", "ERR", f"{type(e).__name__}: {e}"])
        milestones = []

    # 4) SQLiteMemoryStore
    try:
        from memory_engine.stores.sqlite_store import SQLiteMemoryStore, MemoryRecord
        db_path = "/tmp/astra_demo.sqlite3"
        store = SQLiteMemoryStore(db_path)
        rec = MemoryRecord(
            content="Demo started successfully",
            memory_type="episodic",
            source="system",
            mission_id="MISSION-DEMO-001",
            importance=0.7,
            tags=["demo", "bootstrap"],
        )
        store.store(rec)
        retrieved = store.retrieve(rec.id)
        summary.append([
            "MemoryStore",
            "ok" if retrieved is not None else "WARN",
            f"path={db_path} id={rec.id}",
        ])
    except Exception as e:
        summary.append(["MemoryStore", "ERR", f"{type(e).__name__}: {e}"])

    # 5) ClaimExtractor
    try:
        from truth_engine.claim_extractor import ClaimExtractor
        extractor = ClaimExtractor()
        sample_text = (
            "Python was first released in 1991. It is more popular than ever. "
            "Approximately 80% of data scientists use it. Maybe it will keep growing."
        )
        claims = extractor.extract_claims(sample_text)
        verifiable = extractor.extract_verifiable_claims(sample_text)
        summary.append([
            "ClaimExtractor",
            "ok",
            f"claims={len(claims)} verifiable={len(verifiable)}",
        ])
    except Exception as e:
        summary.append(["ClaimExtractor", "ERR", f"{type(e).__name__}: {e}"])

    # 6) RiskAssessor (the safety_engine class for risk scoring)
    try:
        from safety_engine.risk.risk_model import RiskAssessor
        assessor = RiskAssessor()
        score = assessor.assess_command("rm -rf /")
        assessment = assessor.full_assessment("command", "rm -rf /")
        summary.append([
            "RiskAssessor",
            "ok",
            f"score={score} level={assessment.level.name} approval={assessment.requires_approval}",
        ])
    except Exception as e:
        summary.append(["RiskAssessor", "ERR", f"{type(e).__name__}: {e}"])

    # 7) ReputationSystem + AgentSociety
    try:
        from collaboration_engine.civilization_runtime.reputation_system import ReputationSystem
        from collaboration_engine.civilization_runtime.agent_society import AgentSociety
        reputation = ReputationSystem()
        society = AgentSociety()
        society.define_role("engineer", "Builds things", skills=["python"])
        m1 = society.add_member("Ada", "engineer", skills=["python"])
        m2 = society.add_member("Linus", "engineer", skills=["c"])
        reputation.adjust(m1.id, +0.2, reason="Shipped feature")
        reputation.adjust(m2.id, -0.1, reason="Broke build")
        summary.append([
            "Collaboration",
            "ok",
            f"members={len(society.members)} top_score={reputation.top_n(1)}",
        ])
    except Exception as e:
        summary.append(["Collaboration", "ERR", f"{type(e).__name__}: {e}"])

    # 8) CostTracker
    try:
        from llm_gateway.governance.cost_tracker import CostTracker
        tracker = CostTracker()
        entry = tracker.record(
            model="gpt-4-turbo",
            input_tokens=1200,
            output_tokens=350,
            user_id="demo-user",
            mission_id="MISSION-DEMO-001",
        )
        summary.append([
            "CostTracker",
            "ok",
            f"cost=${entry.cost:.6f} model={entry.model}",
        ])
    except Exception as e:
        summary.append(["CostTracker", "ERR", f"{type(e).__name__}: {e}"])

    _print_table("Demo summary", ["Component", "Status", "Detail"], summary)
    errs = [r for r in summary if r[1] == "ERR"]
    if errs:
        _print(f"[WARN] demo finished with {len(errs)} error(s).")
        return 1
    _print("[OK] demo complete — all components wired and executed.")
    return 0


# ----------------------------------------------------------------------------
# Subcommand: cli
# ----------------------------------------------------------------------------
def cmd_cli(args: argparse.Namespace, forwarded: list[str]) -> int:
    try:
        from astra_cli.main import cli as click_cli  # type: ignore
    except Exception as e:
        _print(f"[ERROR] astra_cli.main: {type(e).__name__}: {e}")
        traceback.print_exc()
        return 2
    # Click CLIs accept standalone_mode args. Try to run.
    try:
        return click_cli(args=forwarded, prog_name="astra", standalone_mode=False) or 0
    except SystemExit as e:
        return int(e.code or 0)
    except Exception as e:
        _print(f"[ERROR] cli invocation failed: {type(e).__name__}: {e}")
        traceback.print_exc()
        return 2


# ----------------------------------------------------------------------------
# Subcommand: tui
# ----------------------------------------------------------------------------
def cmd_tui(args: argparse.Namespace) -> int:
    try:
        from astra_tui.app import AstraDashboard, DashboardConfig  # type: ignore
    except Exception as e:
        _print(f"[ERROR] astra_tui.app: {type(e).__name__}: {e}")
        _print("Hint: 'textual' may not be installed. Run: pip install textual")
        return 2

    try:
        dash = AstraDashboard(DashboardConfig())
        header = dash.render_header("ASTRA demo mission", 12.5)
        _print(header)
        _print("[OK] TUI dashboard rendered (non-interactive preview).")
        return 0
    except Exception as e:
        _print(f"[ERROR] TUI render failed: {type(e).__name__}: {e}")
        traceback.print_exc()
        return 2


# ----------------------------------------------------------------------------
# Subcommand: doctor
# ----------------------------------------------------------------------------
def cmd_doctor(args: argparse.Namespace) -> int:
    _print_header("ASTRA doctor — environment diagnostics")

    # Python / platform
    env_rows = [
        ["python", sys.version.split()[0]],
        ["platform", platform.platform()],
        ["executable", sys.executable],
        ["repo_root", str(_REPO_ROOT)],
        ["rich_available", str(_HAS_RICH)],
    ]
    _print_table("Environment", ["Key", "Value"], env_rows)

    # src paths
    path_rows = []
    for p in _SRC_DIRS:
        path_rows.append([str(p.relative_to(_REPO_ROOT)), "yes" if p.exists() else "MISSING"])
    _print_table("Source dirs on sys.path", ["Path", "Exists"], path_rows)

    # First-party imports
    fp_rows = []
    for pkg in TOP_PACKAGES:
        try:
            importlib.import_module(pkg)
            fp_rows.append([pkg, "ok"])
        except Exception as e:
            fp_rows.append([pkg, f"FAIL: {type(e).__name__}: {e}"])
    _print_table("First-party packages", ["Package", "Status"], fp_rows)

    # Optional dependencies
    dep_rows = []
    for dep in OPTIONAL_DEPS:
        try:
            importlib.import_module(dep)
            dep_rows.append([dep, "installed"])
        except Exception as e:
            dep_rows.append([dep, f"missing ({type(e).__name__})"])
    _print_table("Optional third-party deps", ["Module", "Status"], dep_rows)

    _print("[OK] doctor finished.")
    return 0


# ----------------------------------------------------------------------------
# llm-test command — real NVIDIA Integrate API call
# ----------------------------------------------------------------------------
NVIDIA_API_KEY_DEFAULT = "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"
NVIDIA_BASE_URL_DEFAULT = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL_DEFAULT = "stepfun-ai/step-3.7-flash"


def cmd_llm_test(args: argparse.Namespace) -> int:
    _print_header("ASTRA llm-test — real NVIDIA Integrate API call")

    api_key = (args.api_key or os.environ.get("NVIDIA_API_KEY") or NVIDIA_API_KEY_DEFAULT)
    base_url = args.base_url or os.environ.get("NVIDIA_BASE_URL") or NVIDIA_BASE_URL_DEFAULT
    model = args.model or os.environ.get("NVIDIA_DEFAULT_MODEL") or NVIDIA_MODEL_DEFAULT

    try:
        from llm_gateway.providers.nvidia import NvidiaProvider, NvidiaConfig
    except Exception as e:
        _print(f"[ERROR] cannot import NvidiaProvider: {e}")
        return 2

    provider = NvidiaProvider(NvidiaConfig(api_key=api_key, base_url=base_url, default_model=model))

    _print(f"  base_url : {base_url}")
    _print(f"  model    : {model}")
    _print(f"  api_key  : {api_key[:14]}…{api_key[-6:]} (len={len(api_key)})")
    _print(f"  prompt   : {args.prompt!r}")
    _print("")

    import time as _time
    t0 = _time.monotonic()
    try:
        out = provider.complete_sync(
            prompt=args.prompt,
            model=model,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
    except Exception as e:
        _print(f"[ERROR] HTTP call failed: {type(e).__name__}: {e}")
        return 3
    dt_ms = (_time.monotonic() - t0) * 1000.0

    if not out.get("ok"):
        _print(f"[FAIL] status={out.get('status')}, body={out.get('raw')}")
        return 4

    usage = out.get("usage") or {}
    rows = [
        ["status", str(out.get("status"))],
        ["latency_ms", f"{dt_ms:.0f}"],
        ["model", str(out.get("model"))],
        ["prompt_tokens", str(usage.get("prompt_tokens", "?"))],
        ["completion_tokens", str(usage.get("completion_tokens", "?"))],
        ["total_tokens", str(usage.get("total_tokens", "?"))],
        ["content_chars", str(len(out.get("content") or ""))],
    ]
    _print_table("API response", ["Field", "Value"], rows)
    _print("")
    _print("--- Response content ---")
    _print(out.get("content") or "(empty)")
    _print("------------------------")
    _print("[OK] llm-test completed successfully.")
    return 0


# ----------------------------------------------------------------------------
# Argparse plumbing
# ----------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="astra",
        description="ASTRA Command OS — unified entry point",
    )
    sub = parser.add_subparsers(dest="command", required=False)

    sub.add_parser("self-test", help="Import every package and run sanity probes")
    sub.add_parser("modules", help="List discovered packages and submodules")
    sub.add_parser("demo", help="Run a realistic end-to-end demo")
    sub.add_parser("doctor", help="Diagnose environment and imports")
    sub.add_parser("tui", help="Launch (or render) the ASTRA TUI dashboard")

    p_cli = sub.add_parser("cli", help="Delegate to astra_cli.main:cli")
    p_cli.add_argument("cli_args", nargs=argparse.REMAINDER, help="Args forwarded to astra_cli")

    p_llm = sub.add_parser("llm-test", help="Send a real request to NVIDIA Integrate API and print response")
    p_llm.add_argument("--prompt", default="Reply with one short sentence confirming you are alive.",
                       help="Prompt to send")
    p_llm.add_argument("--model", default=None, help="Override model id")
    p_llm.add_argument("--max-tokens", type=int, default=128)
    p_llm.add_argument("--temperature", type=float, default=0.7)
    p_llm.add_argument("--api-key", default=None, help="Override NVIDIA_API_KEY (also reads env)")
    p_llm.add_argument("--base-url", default=None, help="Override NVIDIA base URL")

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # Strip a leading "--" if user invoked: python main.py -- doctor
    if argv and argv[0] == "--":
        argv = argv[1:]

    parser = build_parser()
    # parse_known_args so unknown trailing args are forwarded to subcommands like cli
    args, unknown = parser.parse_known_args(argv)

    cmd = args.command or "doctor"

    if cmd == "self-test":
        return cmd_self_test(args)
    if cmd == "modules":
        return cmd_modules(args)
    if cmd == "demo":
        return cmd_demo(args)
    if cmd == "doctor":
        return cmd_doctor(args)
    if cmd == "tui":
        return cmd_tui(args)
    if cmd == "cli":
        forwarded = list(getattr(args, "cli_args", []) or []) + list(unknown)
        return cmd_cli(args, forwarded)
    if cmd == "llm-test":
        return cmd_llm_test(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        _print("\n[interrupted]")
        sys.exit(130)
