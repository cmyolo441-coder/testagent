"""ASTRA CLI Config — Load/save user configuration."""
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


DEFAULT_CONFIG = {
    "default_model": "claude-opus-4-8",
    "default_provider": "anthropic",
    "default_horizon": "3m",
    "default_verification_level": 2,
    "auto_approve_under": 30,            # auto-approve actions with risk score below this
    "approval_required_above": 60,
    "max_iterations": 50,
    "checkpoint_interval": 10,
    "memory_decay_days": 90,
    "providers": {
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY", "base_url": "https://api.anthropic.com"},
        "openai": {"api_key_env": "OPENAI_API_KEY", "base_url": "https://api.openai.com"},
        "ollama": {"base_url": "http://localhost:11434"},
    },
    "ui": {
        "theme": "dark",
        "show_risk_score": True,
        "show_confidence": True,
    },
}


@dataclass
class AstraConfig:
    path: Path
    data: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "AstraConfig":
        cfg = cls(path=path, data=dict(DEFAULT_CONFIG))
        if path.exists():
            try:
                loaded = json.loads(path.read_text())
                cfg.data = _merge(cfg.data, loaded)
            except Exception:
                pass
        return cfg

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2))

    def get(self, key: str, default: Any = None) -> Any:
        """Dotted key lookup, e.g. cfg.get('ui.theme')."""
        node: Any = self.data
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, key: str, value: Any) -> None:
        node = self.data
        parts = key.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    def to_dict(self) -> dict:
        return dict(self.data)


def _merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out
