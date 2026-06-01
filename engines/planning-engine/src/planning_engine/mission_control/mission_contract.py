"""Mission Contract — Durable mission definition with verification levels"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class VerificationLevel(Enum):
    UNVERIFIED = 0
    INTERNALLY_CONSISTENT = 1
    SOURCE_SUPPORTED = 2
    INDEPENDENTLY_REPRODUCED = 3
    ADVERSARIAL_REVIEWED = 4
    FORMALLY_PROVEN = 5


class MissionStatus(Enum):
    CREATED = "created"
    PLANNING = "planning"
    EXECUTING = "executing"
    PAUSED = "paused"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class MissionContract:
    """Immutable contract defining a mission's scope and constraints."""
    id: str
    goal: str
    horizon: str = "3m"
    agent_count: int = 1
    verification_level: str = "level-2"
    status: MissionStatus = MissionStatus.CREATED
    budget_limit: Optional[float] = None
    max_tokens: Optional[int] = None
    rollback_enabled: bool = True
    checkpoint_interval: int = 10
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = MissionStatus(self.status)

    def can_execute(self) -> tuple[bool, str]:
        if self.status not in (MissionStatus.CREATED, MissionStatus.PLANNING, MissionStatus.PAUSED):
            return False, f"Mission in invalid state: {self.status.value}"
        return True, "ok"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "horizon": self.horizon,
            "agent_count": self.agent_count,
            "verification_level": self.verification_level,
            "status": self.status.value,
            "budget_limit": self.budget_limit,
            "max_tokens": self.max_tokens,
            "rollback_enabled": self.rollback_enabled,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }
