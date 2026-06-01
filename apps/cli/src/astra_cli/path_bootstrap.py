"""Monorepo import bootstrap — adds all engine/service paths to sys.path"""
import sys
from pathlib import Path


def bootstrap_paths():
    root = Path(__file__).resolve().parent.parent.parent.parent
    paths = [
        root / "engines" / "planning-engine" / "src",
        root / "engines" / "truth-engine" / "src",
        root / "engines" / "memory-engine" / "src",
        root / "engines" / "safety-engine" / "src",
        root / "engines" / "agent-engine" / "src",
        root / "engines" / "identity-engine" / "src",
        root / "engines" / "collaboration-engine" / "src",
        root / "engines" / "science-engine" / "src",
        root / "engines" / "math-engine" / "src",
        root / "engines" / "company-builder-engine" / "src",
        root / "engines" / "code-intelligence-engine" / "src",
        root / "engines" / "workflow-engine" / "src",
        root / "engines" / "evaluation-engine" / "src",
        root / "engines" / "simulation-engine" / "src",
        root / "services" / "llm-gateway" / "src",
        root / "services" / "tool-executor" / "src",
        root / "services" / "sandbox-runner" / "src",
        root / "services" / "memory-service" / "src",
        root / "services" / "truth-service" / "src",
    ]
    for p in paths:
        if p.exists() and str(p) not in sys.path:
            sys.path.insert(0, str(p))
