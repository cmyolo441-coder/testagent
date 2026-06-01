"""Memory Browser Widget — Memory list and search interface"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class MemoryEntry:
    id: str = ""
    title: str = ""
    content: str = ""
    memory_type: str = ""
    importance: float = 0.5
    confidence: float = 0.5
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_accessed: Optional[str] = None
    access_count: int = 0


class MemoryBrowser:
    """Memory list and search widget."""

    def __init__(self, max_display: int = 10):
        self.memories: list[MemoryEntry] = []
        self.max_display = max_display
        self.search_query: str = ""
        self.filter_type: str = ""
        self.sort_by: str = "created_at"  # created_at, importance, access_count
        self.sort_desc: bool = True
        self.selected_index: int = 0

    def add_memory(self, title: str, content: str = "",
                   memory_type: str = "episodic", importance: float = 0.5,
                   confidence: float = 0.5, tags: list[str] = None) -> MemoryEntry:
        entry = MemoryEntry(
            id=f"MEM-{len(self.memories) + 1:04d}",
            title=title,
            content=content,
            memory_type=memory_type,
            importance=importance,
            confidence=confidence,
            tags=tags or [],
        )
        self.memories.append(entry)
        return entry

    def search(self, query: str) -> list[MemoryEntry]:
        q = query.lower()
        return [
            m for m in self.memories
            if q in m.title.lower() or q in m.content.lower() or q in " ".join(m.tags).lower()
        ]

    def get_filtered(self) -> list[MemoryEntry]:
        results = list(self.memories)
        if self.search_query:
            results = self.search(self.search_query)
        if self.filter_type:
            results = [m for m in results if m.memory_type == self.filter_type]

        reverse = self.sort_desc
        results.sort(key=lambda m: getattr(m, self.sort_by, m.created_at), reverse=reverse)
        return results

    def get_selected(self) -> Optional[MemoryEntry]:
        filtered = self.get_filtered()
        if 0 <= self.selected_index < len(filtered):
            return filtered[self.selected_index]
        return None

    def select_next(self):
        filtered = self.get_filtered()
        if self.selected_index < len(filtered) - 1:
            self.selected_index += 1

    def select_previous(self):
        if self.selected_index > 0:
            self.selected_index -= 1

    def render_list(self) -> str:
        filtered = self.get_filtered()
        lines = ["┌─ Memory Browser ────────────────────────────────────┐"]
        type_icons = {"episodic": "E", "semantic": "S", "procedural": "P", "working": "W"}
        for i, mem in enumerate(filtered[:self.max_display]):
            icon = type_icons.get(mem.memory_type, "?")
            marker = ">>>" if i == self.selected_index else "   "
            imp = f"{mem.importance:.0%}"
            lines.append(f"│{marker}[{icon}] {mem.title[:28]:<28} {imp:>5} │")
        if not filtered:
            lines.append(f"│ {'No memories found':<52} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_detail(self) -> str:
        mem = self.get_selected()
        if not mem:
            return "  No memory selected"
        lines = [
            "┌─ Memory Detail ────────────────────────────────────┐",
            f"│ ID:         {mem.id:<40} │",
            f"│ Title:      {mem.title[:40]:<40} │",
            f"│ Type:       {mem.memory_type:<40} │",
            f"│ Importance: {mem.importance:<40} │",
            f"│ Confidence: {mem.confidence:<40} │",
            f"│ Tags:       {', '.join(mem.tags)[:40]:<40} │",
            f"│ Created:    {mem.created_at[:19]:<40} │",
            f"│ Accessed:   {mem.access_count:<40} │",
            f"│ Content:    {mem.content[:40]:<40} │",
            "└────────────────────────────────────────────────────┘",
        ]
        return "\n".join(lines)

    def render_search_bar(self) -> str:
        query = self.search_query or "(no filter)"
        type_filter = self.filter_type or "all"
        return f"Search: [{query}]  Type: [{type_filter}]  Sort: [{self.sort_by}]"

    def render(self) -> str:
        parts = [
            self.render_search_bar(),
            "",
            self.render_list(),
            "",
            self.render_detail(),
        ]
        return "\n".join(parts)

    def get_stats(self) -> dict:
        filtered = self.get_filtered()
        types = {}
        for m in self.memories:
            types[m.memory_type] = types.get(m.memory_type, 0) + 1
        return {
            "total_memories": len(self.memories),
            "filtered_count": len(filtered),
            "type_distribution": types,
            "selected_index": self.selected_index,
        }
