"""Memory Versioning — Track memory changes over time"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid
import hashlib
import json


@dataclass
class MemoryVersion:
    version_id: str = field(default_factory=lambda: f"VER-{uuid.uuid4().hex[:12]}")
    memory_id: str = ""
    version_number: int = 1
    content: str = ""
    context: dict = field(default_factory=dict)
    importance: float = 0.5
    confidence: float = 0.5
    tags: list[str] = field(default_factory=list)
    change_summary: str = ""
    changed_by: str = ""  # agent_id, user_id, or "system"
    change_type: str = ""  # created, updated, merged, archived
    content_hash: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "version_id": self.version_id,
            "memory_id": self.memory_id,
            "version_number": self.version_number,
            "content": self.content[:200],
            "change_summary": self.change_summary,
            "change_type": self.change_type,
            "created_at": self.created_at,
        }


class MemoryVersioning:
    """Tracks memory versions and history of changes."""

    def __init__(self, store=None):
        self.store = store
        self.versions: dict[str, MemoryVersion] = {}
        self._memory_versions: dict[str, list[str]] = {}

    def version(self, memory_id: str, content: str, context: dict = None,
                importance: float = 0.5, confidence: float = 0.5,
                tags: list[str] = None, change_summary: str = "",
                changed_by: str = "system", change_type: str = "created") -> MemoryVersion:
        existing_versions = self._memory_versions.get(memory_id, [])
        version_number = len(existing_versions) + 1

        content_hash = self._hash_content(content)

        if existing_versions and change_type == "created":
            latest = self.versions.get(existing_versions[-1])
            if latest and latest.content_hash == content_hash:
                return latest

        mv = MemoryVersion(
            memory_id=memory_id,
            version_number=version_number,
            content=content,
            context=context or {},
            importance=importance,
            confidence=confidence,
            tags=tags or [],
            change_summary=change_summary,
            changed_by=changed_by,
            change_type=change_type,
            content_hash=content_hash,
        )
        self.versions[mv.version_id] = mv

        if memory_id not in self._memory_versions:
            self._memory_versions[memory_id] = []
        self._memory_versions[memory_id].append(mv.version_id)

        if self.store:
            from memory_engine.stores.sqlite_store import MemoryRecord
            record = MemoryRecord(
                memory_type="version",
                content=f"Version {version_number} of {memory_id}: {change_summary}",
                context={"memory_id": memory_id, "version_number": version_number},
                importance=importance,
                tags=tags or [],
                metadata={"version_id": mv.version_id},
            )
            self.store.store(record)

        return mv

    def get_versions(self, memory_id: str) -> list[MemoryVersion]:
        version_ids = self._memory_versions.get(memory_id, [])
        return [self.versions[vid] for vid in version_ids if vid in self.versions]

    def get_version(self, version_id: str) -> Optional[MemoryVersion]:
        return self.versions.get(version_id)

    def get_latest_version(self, memory_id: str) -> Optional[MemoryVersion]:
        version_ids = self._memory_versions.get(memory_id, [])
        if not version_ids:
            return None
        return self.versions.get(version_ids[-1])

    def compare_versions(self, version_id_a: str, version_id_b: str) -> dict:
        va = self.versions.get(version_id_a)
        vb = self.versions.get(version_id_b)
        if not va or not vb:
            return {"error": "One or both versions not found"}

        content_changed = va.content != vb.content
        context_changed = va.context != vb.context
        importance_changed = va.importance != vb.importance

        return {
            "version_a": va.to_dict(),
            "version_b": vb.to_dict(),
            "content_changed": content_changed,
            "context_changed": context_changed,
            "importance_changed": importance_changed,
            "importance_delta": vb.importance - va.importance,
            "same_content_hash": va.content_hash == vb.content_hash,
        }

    def revert_to(self, version_id: str) -> Optional[MemoryVersion]:
        target = self.versions.get(version_id)
        if not target:
            return None
        return self.version(
            memory_id=target.memory_id,
            content=target.content,
            context=target.context,
            importance=target.importance,
            confidence=target.confidence,
            tags=target.tags,
            change_summary=f"Reverted to version {target.version_number}",
            changed_by="system",
            change_type="reverted",
        )

    def get_change_history(self, memory_id: str) -> list[dict]:
        versions = self.get_versions(memory_id)
        return [
            {
                "version": v.version_number,
                "change_type": v.change_type,
                "change_summary": v.change_summary,
                "changed_by": v.changed_by,
                "timestamp": v.created_at,
            }
            for v in versions
        ]

    def _hash_content(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_stats(self) -> dict:
        all_versions = list(self.versions.values())
        by_change_type = {}
        for v in all_versions:
            by_change_type[v.change_type] = by_change_type.get(v.change_type, 0) + 1
        return {
            "total_versions": len(all_versions),
            "memories_with_versions": len(self._memory_versions),
            "by_change_type": by_change_type,
        }
