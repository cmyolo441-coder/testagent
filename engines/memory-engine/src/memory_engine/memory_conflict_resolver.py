"""Memory Conflict Resolver — Detect and resolve conflicting memories"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class MemoryConflict:
    id: str = field(default_factory=lambda: f"CFM-{uuid.uuid4().hex[:12]}")
    memory_a_id: str = ""
    memory_b_id: str = ""
    conflict_type: str = ""  # contradiction, duplication, inconsistency, temporal
    description: str = ""
    severity: str = "medium"  # low, medium, high
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ConflictResolution:
    conflict_id: str
    strategy: str  # keep_newer, keep_older, keep_higher_confidence, merge, manual
    resolved_memory_id: Optional[str] = None
    discarded_memory_id: Optional[str] = None
    merged_content: Optional[str] = None
    resolution_notes: str = ""
    resolved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MemoryConflictResolver:
    """Detects and resolves conflicting memories."""

    STRATEGIES = {
        "keep_newer": "Keep the most recently created/updated memory",
        "keep_older": "Keep the oldest memory (original truth)",
        "keep_higher_confidence": "Keep the memory with higher confidence score",
        "merge": "Merge both memories into a combined record",
        "manual": "Flag for manual resolution",
    }

    def __init__(self, store=None):
        self.store = store
        self.conflicts: dict[str, MemoryConflict] = {}
        self.resolutions: dict[str, ConflictResolution] = {}

    def detect_conflicts(self, memories: list[dict]) -> list[MemoryConflict]:
        conflicts = []
        for i, mem_a in enumerate(memories):
            for mem_b in memories[i + 1:]:
                conflict = self._check_conflict(mem_a, mem_b)
                if conflict:
                    conflicts.append(conflict)
                    self.conflicts[conflict.id] = conflict
        return conflicts

    def _check_conflict(self, mem_a: dict, mem_b: dict) -> Optional[MemoryConflict]:
        content_a = mem_a.get("content", "")
        content_b = mem_b.get("content", "")
        id_a = mem_a.get("id", "")
        id_b = mem_b.get("id", "")

        if self._are_contradictory(mem_a, mem_b):
            return MemoryConflict(
                memory_a_id=id_a,
                memory_b_id=id_b,
                conflict_type="contradiction",
                description=f"Contradictory statements: '{content_a[:50]}' vs '{content_b[:50]}'",
                severity="high",
            )

        if self._are_duplicated(mem_a, mem_b):
            return MemoryConflict(
                memory_a_id=id_a,
                memory_b_id=id_b,
                conflict_type="duplication",
                description=f"Duplicate content: '{content_a[:50]}'",
                severity="low",
            )

        if self._are_inconsistent(mem_a, mem_b):
            return MemoryConflict(
                memory_a_id=id_a,
                memory_b_id=id_b,
                conflict_type="inconsistency",
                description=f"Inconsistent data: '{content_a[:50]}' vs '{content_b[:50]}'",
                severity="medium",
            )

        return None

    def _are_contradictory(self, a: dict, b: dict) -> bool:
        a_ctx = a.get("context", {})
        b_ctx = b.get("context", {})
        if a.get("memory_type") == "semantic" and b.get("memory_type") == "semantic":
            a_pred = a_ctx.get("predicate", "")
            b_pred = b_ctx.get("predicate", "")
            if a.get("content", "").split()[0:2] == b.get("content", "").split()[0:2]:
                if a_pred and b_pred and a_pred != b_pred:
                    return True
        negation_words = {"not", "no", "never", "false", "failed", "error"}
        a_words = set(a.get("content", "").lower().split())
        b_words = set(b.get("content", "").lower().split())
        if a_words & negation_words and not (b_words & negation_words):
            common = a.get("content", "").lower().split()[:3]
            if common == b.get("content", "").lower().split()[:3]:
                return True
        return False

    def _are_duplicated(self, a: dict, b: dict) -> bool:
        a_words = set(a.get("content", "").lower().split())
        b_words = set(b.get("content", "").lower().split())
        if not a_words or not b_words:
            return False
        overlap = len(a_words & b_words) / max(len(a_words), len(b_words))
        return overlap > 0.9

    def _are_inconsistent(self, a: dict, b: dict) -> bool:
        a_ctx = a.get("context", {})
        b_ctx = b.get("context", {})
        for key in ("subject", "entity"):
            if key in a_ctx and key in b_ctx:
                if a_ctx[key] == b_ctx[key]:
                    for vkey in ("value", "object", "state"):
                        if vkey in a_ctx and vkey in b_ctx:
                            if a_ctx[vkey] != b_ctx[vkey]:
                                return True
        return False

    def resolve(self, conflicts: list[MemoryConflict],
                strategy: str = "keep_newer",
                memories: dict = None) -> list[ConflictResolution]:
        resolutions = []
        for conflict in conflicts:
            resolution = self._resolve_single(conflict, strategy, memories)
            if resolution:
                resolutions.append(resolution)
                self.resolutions[conflict.id] = resolution
        return resolutions

    def _resolve_single(self, conflict: MemoryConflict, strategy: str,
                        memories: dict = None) -> Optional[ConflictResolution]:
        if not memories:
            return ConflictResolution(
                conflict_id=conflict.id,
                strategy=strategy,
                resolution_notes="No memory data available for resolution",
            )

        mem_a = memories.get(conflict.memory_a_id)
        mem_b = memories.get(conflict.memory_b_id)

        if not mem_a or not mem_b:
            return ConflictResolution(
                conflict_id=conflict.id,
                strategy=strategy,
                resolution_notes="One or both memories not found",
            )

        if strategy == "keep_newer":
            if mem_a.get("created_at", "") >= mem_b.get("created_at", ""):
                resolved_id, discarded_id = conflict.memory_a_id, conflict.memory_b_id
            else:
                resolved_id, discarded_id = conflict.memory_b_id, conflict.memory_a_id
            return ConflictResolution(
                conflict_id=conflict.id,
                strategy=strategy,
                resolved_memory_id=resolved_id,
                discarded_memory_id=discarded_id,
            )

        elif strategy == "keep_older":
            if mem_a.get("created_at", "") <= mem_b.get("created_at", ""):
                resolved_id, discarded_id = conflict.memory_a_id, conflict.memory_b_id
            else:
                resolved_id, discarded_id = conflict.memory_b_id, conflict.memory_a_id
            return ConflictResolution(
                conflict_id=conflict.id,
                strategy=strategy,
                resolved_memory_id=resolved_id,
                discarded_memory_id=discarded_id,
            )

        elif strategy == "keep_higher_confidence":
            conf_a = mem_a.get("confidence", 0.5)
            conf_b = mem_b.get("confidence", 0.5)
            if conf_a >= conf_b:
                resolved_id, discarded_id = conflict.memory_a_id, conflict.memory_b_id
            else:
                resolved_id, discarded_id = conflict.memory_b_id, conflict.memory_a_id
            return ConflictResolution(
                conflict_id=conflict.id,
                strategy=strategy,
                resolved_memory_id=resolved_id,
                discarded_memory_id=discarded_id,
            )

        elif strategy == "merge":
            merged = f"{mem_a.get('content', '')} | {mem_b.get('content', '')}"
            return ConflictResolution(
                conflict_id=conflict.id,
                strategy=strategy,
                merged_content=merged,
                resolution_notes="Merged both memories",
            )

        return ConflictResolution(
            conflict_id=conflict.id,
            strategy="manual",
            resolution_notes="Flagged for manual resolution",
        )

    def get_unresolved(self) -> list[MemoryConflict]:
        return [
            c for c in self.conflicts.values()
            if c.id not in self.resolutions
        ]

    def get_stats(self) -> dict:
        conflicts = list(self.conflicts.values())
        resolutions = list(self.resolutions.values())
        by_type = {}
        for c in conflicts:
            by_type[c.conflict_type] = by_type.get(c.conflict_type, 0) + 1
        return {
            "total_conflicts": len(conflicts),
            "resolved": len(resolutions),
            "unresolved": len(conflicts) - len(resolutions),
            "by_type": by_type,
        }
