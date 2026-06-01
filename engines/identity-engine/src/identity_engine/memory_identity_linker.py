"""Memory ↔ Identity Linker — Tag memory records with identity facets."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


VALID_FACET_KINDS = {"value", "commitment", "promise", "rule", "style", "manifest"}


@dataclass
class IdentityLink:
    id: str = field(default_factory=lambda: f"LINK-{uuid.uuid4().hex[:10]}")
    memory_id: str = ""
    facet_kind: str = "value"  # value, commitment, promise, rule, style, manifest
    facet_id: str = ""
    weight: float = 1.0
    note: str = ""
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "memory_id": self.memory_id,
            "facet_kind": self.facet_kind,
            "facet_id": self.facet_id,
            "weight": self.weight,
            "note": self.note,
            "created_at": self.created_at,
        }


class MemoryIdentityLinker:
    """Bidirectional index between memory record IDs and identity facets."""

    def __init__(self):
        self.links: dict[str, IdentityLink] = {}
        self.by_memory: dict[str, set[str]] = {}  # memory_id -> link_ids
        self.by_facet: dict[tuple[str, str], set[str]] = {}  # (kind, facet_id) -> link_ids

    def link(self, memory_id: str, facet_kind: str, facet_id: str,
             weight: float = 1.0, note: str = "") -> IdentityLink:
        if facet_kind not in VALID_FACET_KINDS:
            raise ValueError(
                f"Unknown facet_kind '{facet_kind}'. Expected one of {sorted(VALID_FACET_KINDS)}."
            )
        link = IdentityLink(
            memory_id=memory_id,
            facet_kind=facet_kind,
            facet_id=facet_id,
            weight=weight,
            note=note,
        )
        self.links[link.id] = link
        self.by_memory.setdefault(memory_id, set()).add(link.id)
        self.by_facet.setdefault((facet_kind, facet_id), set()).add(link.id)
        return link

    def unlink(self, link_id: str) -> bool:
        link = self.links.pop(link_id, None)
        if not link:
            return False
        mem_set = self.by_memory.get(link.memory_id)
        if mem_set:
            mem_set.discard(link_id)
            if not mem_set:
                del self.by_memory[link.memory_id]
        key = (link.facet_kind, link.facet_id)
        f_set = self.by_facet.get(key)
        if f_set:
            f_set.discard(link_id)
            if not f_set:
                del self.by_facet[key]
        return True

    def facets_for_memory(self, memory_id: str) -> list[IdentityLink]:
        ids = self.by_memory.get(memory_id, set())
        return [self.links[i] for i in ids if i in self.links]

    def memories_for_facet(self, facet_kind: str, facet_id: str) -> list[str]:
        ids = self.by_facet.get((facet_kind, facet_id), set())
        return sorted({self.links[i].memory_id for i in ids if i in self.links})

    def tag_memory(self, memory_record, facet_kind: str, facet_id: str,
                   weight: float = 1.0, note: str = "") -> IdentityLink:
        """Helper that links a MemoryRecord-like object and appends a tag.

        Works with anything having an ``id`` attribute and an optional
        ``tags`` list attribute (e.g., ``MemoryRecord`` from memory-engine).
        """
        memory_id = getattr(memory_record, "id", None) or str(memory_record)
        tags = getattr(memory_record, "tags", None)
        tag_label = f"{facet_kind}:{facet_id}"
        if isinstance(tags, list) and tag_label not in tags:
            tags.append(tag_label)
        return self.link(memory_id, facet_kind, facet_id, weight=weight, note=note)

    def stats(self) -> dict:
        by_kind: dict[str, int] = {}
        for link in self.links.values():
            by_kind[link.facet_kind] = by_kind.get(link.facet_kind, 0) + 1
        return {
            "total_links": len(self.links),
            "memories_indexed": len(self.by_memory),
            "facets_indexed": len(self.by_facet),
            "by_kind": by_kind,
        }
