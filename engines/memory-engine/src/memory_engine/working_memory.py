"""Working Memory — Active context for current conversation/task"""
from collections import deque
from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class WorkingMemoryItem:
    role: str  # user, assistant, tool, system
    content: str
    metadata: dict = field(default_factory=dict)


class WorkingMemory:
    """Bounded working memory with priority-based eviction."""

    def __init__(self, max_items: int = 50, max_tokens: int = 8000):
        self.max_items = max_items
        self.max_tokens = max_tokens
        self.items: deque[WorkingMemoryItem] = deque(maxlen=max_items)
        self.pinned: list[WorkingMemoryItem] = []
        self.token_count = 0

    def add(self, role: str, content: str, metadata: dict = None, pin: bool = False):
        item = WorkingMemoryItem(role=role, content=content, metadata=metadata or {})
        tokens = self._estimate_tokens(content)

        if pin:
            self.pinned.append(item)
            self.token_count += tokens
        else:
            if len(self.items) >= self.max_items:
                removed = self.items.popleft()
                self.token_count -= self._estimate_tokens(removed.content)
            self.items.append(item)
            self.token_count += tokens

        self._enforce_token_limit()

    def get_context(self) -> list[dict]:
        context = []
        for item in self.pinned:
            context.append({"role": item.role, "content": item.content})
        for item in self.items:
            context.append({"role": item.role, "content": item.content})
        return context

    def get_recent(self, n: int = 10) -> list[WorkingMemoryItem]:
        all_items = list(self.items)
        return all_items[-n:]

    def clear(self):
        self.items.clear()
        self.pinned.clear()
        self.token_count = 0

    def summarize(self) -> str:
        if not self.items and not self.pinned:
            return "Empty working memory"
        pinned_count = len(self.pinned)
        total = len(self.items) + pinned_count
        return f"Working memory: {total} items ({pinned_count} pinned), ~{self.token_count} tokens"

    def to_dict(self) -> dict:
        return {
            "pinned": [{"role": i.role, "content": i.content[:100]} for i in self.pinned],
            "recent": [{"role": i.role, "content": i.content[:100]} for i in list(self.items)[-5:]],
            "token_count": self.token_count,
            "item_count": len(self.items) + len(self.pinned),
        }

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def _enforce_token_limit(self):
        while self.token_count > self.max_tokens and self.items:
            removed = self.items.popleft()
            self.token_count -= self._estimate_tokens(removed.content)
