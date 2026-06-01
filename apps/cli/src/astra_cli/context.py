"""ASTRA CLI Context — holds session state and configuration"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import os


@dataclass
class AstraContext:
    """Runtime context for CLI commands."""
    workspace: Path = field(default_factory=lambda: Path.cwd())
    astra_dir: Path = field(default=None)
    config_path: Path = field(default=None)
    verbose: bool = False
    dry_run: bool = False
    session_id: Optional[str] = None

    def __post_init__(self):
        if self.astra_dir is None:
            self.astra_dir = self.workspace / ".astra"
        if self.config_path is None:
            self.config_path = self.astra_dir / "config.json"

    def ensure_dirs(self):
        self.astra_dir.mkdir(parents=True, exist_ok=True)
        (self.astra_dir / "memory").mkdir(exist_ok=True)
        (self.astra_dir / "checkpoints").mkdir(exist_ok=True)
        (self.astra_dir / "audit").mkdir(exist_ok=True)

    @property
    def db_path(self) -> Path:
        return self.astra_dir / "astra.sqlite3"
