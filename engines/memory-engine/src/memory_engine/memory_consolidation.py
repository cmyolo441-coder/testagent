"""Memory Consolidation — Merge, compress, and optimize memories"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class ConsolidationResult:
    id: str
    source_ids: list[str]
    result_id: Optional[str]
    strategy: str
    summary: str
    compression_ratio: float
    created_at: str


class MemoryConsolidator:
    """Consolidate and compress memories to save space and improve retrieval."""

    STRATEGIES = {
        "merge_duplicates": "Merge near-duplicate memories into one",
        "summarize_cluster": "Summarize a cluster of related memories",
        "forget_unimportant": "Remove low-importance, old memories",
        "promote_frequent": "Promote frequently accessed memories",
        "archive_old": "Archive old memories to cold storage",
    }

    def __init__(self, store):
        self.store = store

    def consolidate(self, strategy: str, memory_ids: list[str] = None,
                    mission_id: str = None) -> ConsolidationResult:
        if strategy == "merge_duplicates":
            return self._merge_duplicates(memory_ids)
        elif strategy == "forget_unimportant":
            return self._forget_unimportant(mission_id)
        elif strategy == "promote_frequent":
            return self._promote_frequent(mission_id)
        elif strategy == "summarize_cluster":
            return self._summarize_cluster(memory_ids)
        else:
            return ConsolidationResult(
                id=f"CON-{uuid.uuid4().hex[:8]}",
                source_ids=memory_ids or [],
                result_id=None,
                strategy=strategy,
                summary=f"Unknown strategy: {strategy}",
                compression_ratio=1.0,
                created_at=datetime.now(timezone.utc).isoformat(),
            )

    def _merge_duplicates(self, memory_ids: list[str] = None) -> ConsolidationResult:
        # Find duplicates based on content similarity
        all_memories = self.store.search(limit=1000) if not memory_ids else [
            self.store.retrieve(mid) for mid in memory_ids
        ]
        all_memories = [m for m in all_memories if m]

        merged = 0
        for i, mem_a in enumerate(all_memories):
            for mem_b in all_memories[i + 1:]:
                if self._are_similar(mem_a.content, mem_b.content):
                    mem_a.importance = max(mem_a.importance, mem_b.importance)
                    mem_a.access_count += mem_b.access_count
                    self.store.store(mem_a)
                    self.store.delete(mem_b.id)
                    merged += 1

        return ConsolidationResult(
            id=f"CON-{uuid.uuid4().hex[:8]}",
            source_ids=[m.id for m in all_memories],
            result_id=None,
            strategy="merge_duplicates",
            summary=f"Merged {merged} duplicate memories",
            compression_ratio=merged / len(all_memories) if all_memories else 1.0,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def _forget_unimportant(self, mission_id: str = None) -> ConsolidationResult:
        memories = self.store.search(mission_id=mission_id, limit=10000)
        forgotten = 0
        for mem in memories:
            if mem.importance < 0.2 and mem.access_count == 0:
                self.store.delete(mem.id)
                forgotten += 1

        return ConsolidationResult(
            id=f"CON-{uuid.uuid4().hex[:8]}",
            source_ids=[],
            result_id=None,
            strategy="forget_unimportant",
            summary=f"Forgot {forgotten} unimportant memories",
            compression_ratio=forgotten / len(memories) if memories else 0,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def _promote_frequent(self, mission_id: str = None) -> ConsolidationResult:
        memories = self.store.search(mission_id=mission_id, limit=10000)
        promoted = 0
        for mem in memories:
            if mem.access_count > 5 and mem.importance < 0.8:
                mem.importance = min(1.0, mem.importance + 0.2)
                self.store.store(mem)
                promoted += 1

        return ConsolidationResult(
            id=f"CON-{uuid.uuid4().hex[:8]}",
            source_ids=[],
            result_id=None,
            strategy="promote_frequent",
            summary=f"Promoted {promoted} frequently accessed memories",
            compression_ratio=1.0,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def _summarize_cluster(self, memory_ids: list[str]) -> ConsolidationResult:
        memories = [self.store.retrieve(mid) for mid in memory_ids]
        memories = [m for m in memories if m]
        if not memories:
            return ConsolidationResult(
                id=f"CON-{uuid.uuid4().hex[:8]}",
                source_ids=memory_ids,
                result_id=None,
                strategy="summarize_cluster",
                summary="No memories to summarize",
                compression_ratio=1.0,
                created_at=datetime.now(timezone.utc).isoformat(),
            )

        combined_content = "\n".join(m.content for m in memories)
        summary = f"Summary of {len(memories)} related memories"

        from memory_engine.stores.sqlite_store import MemoryRecord
        result_record = MemoryRecord(
            memory_type="semantic",
            content=summary,
            importance=max(m.importance for m in memories),
            confidence=min(m.confidence for m in memories),
            tags=list(set(t for m in memories for t in m.tags)),
        )
        self.store.store(result_record)

        for mem in memories:
            self.store.delete(mem.id)

        return ConsolidationResult(
            id=f"CON-{uuid.uuid4().hex[:8]}",
            source_ids=memory_ids,
            result_id=result_record.id,
            strategy="summarize_cluster",
            summary=f"Summarized {len(memories)} memories into one",
            compression_ratio=(len(memories) - 1) / len(memories),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def _are_similar(self, a: str, b: str, threshold: float = 0.8) -> bool:
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        if not words_a or not words_b:
            return False
        overlap = len(words_a & words_b) / max(len(words_a), len(words_b))
        return overlap >= threshold
