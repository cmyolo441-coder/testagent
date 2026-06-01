"""Identity Manifest — Core identity document for an ASTRA agent."""
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class IdentityManifest:
    """Canonical identity record for an agent."""

    id: str = field(default_factory=lambda: f"IDENTITY-{uuid.uuid4().hex[:12]}")
    name: str = "ASTRA Agent"
    mission_statement: str = ""
    core_values: list[str] = field(default_factory=list)
    communication_style_id: Optional[str] = None
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    owner_user_id: Optional[str] = None
    version: int = 1
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "mission_statement": self.mission_statement,
            "core_values": list(self.core_values),
            "communication_style_id": self.communication_style_id,
            "allowed_actions": list(self.allowed_actions),
            "forbidden_actions": list(self.forbidden_actions),
            "owner_user_id": self.owner_user_id,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IdentityManifest":
        return cls(
            id=data.get("id", f"IDENTITY-{uuid.uuid4().hex[:12]}"),
            name=data.get("name", "ASTRA Agent"),
            mission_statement=data.get("mission_statement", ""),
            core_values=list(data.get("core_values", [])),
            communication_style_id=data.get("communication_style_id"),
            allowed_actions=list(data.get("allowed_actions", [])),
            forbidden_actions=list(data.get("forbidden_actions", [])),
            owner_user_id=data.get("owner_user_id"),
            version=int(data.get("version", 1)),
            created_at=data.get("created_at", _now_iso()),
            updated_at=data.get("updated_at", _now_iso()),
            metadata=dict(data.get("metadata", {})),
        )

    def save(self, path: str | Path) -> str:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2))
        return str(p)

    @classmethod
    def load(cls, path: str | Path) -> "IdentityManifest":
        p = Path(path)
        return cls.from_dict(json.loads(p.read_text()))

    def bump_version(self) -> int:
        self.version += 1
        self.updated_at = _now_iso()
        return self.version
