"""Memory Consolidation — Group co-occurring memories into consolidation notes."""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
from collections import defaultdict
import uuid


@dataclass
class MemoryRecord:
    id: str = field(default_factory=lambda: f"MEM-{uuid.uuid4().hex[:8]}")
    content: str = ""
    tags: list[str] = field(default_factory=list)
    mission_id: Optional[str] = None
    importance: float = 0.5
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ConsolidationProposal:
    id: str = field(default_factory=lambda: f"CON-{uuid.uuid4().hex[:8]}")
    summary: str = ""
    source_ids: list[str] = field(default_factory=list)
    importance: float = 0.5
    tags: list[str] = field(default_factory=list)
    mission_id: Optional[str] = None
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MemoryConsolidator:
    """Scheduled job that groups frequent co-occurring memories and produces consolidation notes."""

    def __init__(self, min_group_size: int = 2, max_summary_chars: int = 240):
        self.min_group_size = int(min_group_size)
        self.max_summary_chars = int(max_summary_chars)
        self.proposals: list[ConsolidationProposal] = []

    def _group_by_mission(self, records: list[MemoryRecord]) -> dict[str, list[MemoryRecord]]:
        groups: dict[str, list[MemoryRecord]] = defaultdict(list)
        for r in records:
            if r.mission_id:
                groups[f"mission:{r.mission_id}"].append(r)
        return groups

    def _group_by_tag(self, records: list[MemoryRecord]) -> dict[str, list[MemoryRecord]]:
        groups: dict[str, list[MemoryRecord]] = defaultdict(list)
        for r in records:
            for tag in r.tags:
                groups[f"tag:{tag}"].append(r)
        return groups

    def _summarize(self, records: list[MemoryRecord]) -> str:
        snippets = []
        for r in records:
            text = (r.content or "").strip().replace("\n", " ")
            if text:
                snippets.append(text)
        joined = " | ".join(snippets)
        if len(joined) > self.max_summary_chars:
            joined = joined[: self.max_summary_chars - 3] + "..."
        return joined

    def run(self, records: list[MemoryRecord]) -> list[ConsolidationProposal]:
        proposals: list[ConsolidationProposal] = []
        seen_groups: set[frozenset[str]] = set()

        groupings: dict[str, list[MemoryRecord]] = {}
        groupings.update(self._group_by_mission(records))
        groupings.update(self._group_by_tag(records))

        for key, group in groupings.items():
            if len(group) < self.min_group_size:
                continue
            ids = frozenset(r.id for r in group)
            if ids in seen_groups:
                continue
            seen_groups.add(ids)

            avg_importance = sum(r.importance for r in group) / len(group)
            tags = sorted({t for r in group for t in r.tags})
            mission_id = next((r.mission_id for r in group if r.mission_id), None)

            proposal = ConsolidationProposal(
                summary=f"[{key}] {self._summarize(group)}",
                source_ids=[r.id for r in group],
                importance=min(1.0, avg_importance + 0.1),
                tags=tags,
                mission_id=mission_id,
            )
            proposals.append(proposal)

        self.proposals.extend(proposals)
        return proposals

    def to_dict(self) -> dict:
        return {
            "min_group_size": self.min_group_size,
            "proposals": len(self.proposals),
        }
