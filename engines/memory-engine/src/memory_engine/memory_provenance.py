"""Memory Provenance — Track memory sources and origins"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class ProvenanceRecord:
    id: str = field(default_factory=lambda: f"PRV-{uuid.uuid4().hex[:12]}")
    memory_id: str = ""
    source: str = ""  # user_input, tool_output, agent_reasoning, external_api, system
    source_detail: str = ""
    reason: str = ""
    confidence: float = 1.0
    chain: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "memory_id": self.memory_id,
            "source": self.source,
            "source_detail": self.source_detail,
            "reason": self.reason,
            "confidence": self.confidence,
            "chain_length": len(self.chain),
            "created_at": self.created_at,
        }


class MemoryProvenance:
    """Tracks the provenance and lineage of memories."""

    def __init__(self, store=None):
        self.store = store
        self.records: dict[str, ProvenanceRecord] = {}
        self._memory_index: dict[str, list[str]] = {}

    def track(self, memory_id: str, source: str, reason: str = "",
              source_detail: str = "", confidence: float = 1.0,
              parent_provenance_id: str = None,
              metadata: dict = None) -> ProvenanceRecord:
        chain = []
        if parent_provenance_id:
            parent = self.records.get(parent_provenance_id)
            if parent:
                chain = list(parent.chain)
                chain.append({
                    "provenance_id": parent.id,
                    "source": parent.source,
                    "memory_id": parent.memory_id,
                    "timestamp": parent.created_at,
                })

        record = ProvenanceRecord(
            memory_id=memory_id,
            source=source,
            source_detail=source_detail,
            reason=reason,
            confidence=confidence,
            chain=chain,
            metadata=metadata or {},
        )
        self.records[record.id] = record

        if memory_id not in self._memory_index:
            self._memory_index[memory_id] = []
        self._memory_index[memory_id].append(record.id)

        if self.store:
            from memory_engine.stores.sqlite_store import MemoryRecord
            mem_record = MemoryRecord(
                memory_type="provenance",
                content=f"Provenance: {memory_id} from {source}",
                context={"source": source, "reason": reason},
                importance=confidence * 0.5,
                metadata={"provenance_id": record.id, "memory_id": memory_id},
            )
            self.store.store(mem_record)

        return record

    def get_provenance(self, memory_id: str) -> list[ProvenanceRecord]:
        record_ids = self._memory_index.get(memory_id, [])
        return [self.records[rid] for rid in record_ids if rid in self.records]

    def get_lineage(self, memory_id: str) -> list[dict]:
        provenances = self.get_provenance(memory_id)
        if not provenances:
            return []
        latest = provenances[-1]
        lineage = []
        for entry in latest.chain:
            lineage.append(entry)
        lineage.append({
            "provenance_id": latest.id,
            "source": latest.source,
            "memory_id": memory_id,
            "timestamp": latest.created_at,
        })
        return lineage

    def get_by_source(self, source: str) -> list[ProvenanceRecord]:
        return [r for r in self.records.values() if r.source == source]

    def verify_chain(self, memory_id: str) -> dict:
        provenances = self.get_provenance(memory_id)
        if not provenances:
            return {"verified": False, "reason": "No provenance records found"}

        latest = provenances[-1]
        chain_valid = True
        for i, entry in enumerate(latest.chain):
            if "source" not in entry or "memory_id" not in entry:
                chain_valid = False
                break

        return {
            "verified": chain_valid,
            "chain_length": len(latest.chain),
            "source": latest.source,
            "confidence": latest.confidence,
            "total_provenance_records": len(provenances),
        }

    def get_statistics(self) -> dict:
        records = list(self.records.values())
        by_source = {}
        for r in records:
            by_source[r.source] = by_source.get(r.source, 0) + 1
        avg_confidence = sum(r.confidence for r in records) / len(records) if records else 0
        return {
            "total_provenance_records": len(records),
            "memories_tracked": len(self._memory_index),
            "by_source": by_source,
            "avg_confidence": round(avg_confidence, 3),
        }

    def get_stats(self) -> dict:
        return self.get_statistics()
