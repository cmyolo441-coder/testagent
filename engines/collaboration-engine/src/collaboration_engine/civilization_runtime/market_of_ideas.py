"""Market of Ideas — Agents post ideas, vote, and prices move with demand."""
from dataclasses import dataclass, field
from typing import Optional
import time
import uuid


@dataclass
class Idea:
    id: str = field(default_factory=lambda: f"IDEA-{uuid.uuid4().hex[:8]}")
    author: str = ""
    text: str = ""
    tags: list[str] = field(default_factory=list)
    upvotes: int = 0
    downvotes: int = 0
    price: float = 1.0
    voters: dict[str, int] = field(default_factory=dict)  # voter_id -> +1/-1
    created_at: float = field(default_factory=time.time)


class MarketOfIdeas:
    """Idea bazaar with simple supply/demand price discovery."""

    def __init__(self, base_price: float = 1.0, sensitivity: float = 0.1):
        self.base_price = base_price
        self.sensitivity = sensitivity
        self.ideas: dict[str, Idea] = {}

    def post(self, author: str, text: str, tags: Optional[list[str]] = None) -> Idea:
        idea = Idea(author=author, text=text, tags=list(tags or []), price=self.base_price)
        self.ideas[idea.id] = idea
        return idea

    def upvote(self, idea_id: str, voter_id: str) -> Optional[Idea]:
        return self._vote(idea_id, voter_id, +1)

    def downvote(self, idea_id: str, voter_id: str) -> Optional[Idea]:
        return self._vote(idea_id, voter_id, -1)

    def _vote(self, idea_id: str, voter_id: str, direction: int) -> Optional[Idea]:
        idea = self.ideas.get(idea_id)
        if not idea:
            return None
        prev = idea.voters.get(voter_id, 0)
        if prev == direction:
            return idea  # idempotent
        # undo previous vote
        if prev == +1:
            idea.upvotes -= 1
        elif prev == -1:
            idea.downvotes -= 1
        # apply new
        if direction == +1:
            idea.upvotes += 1
        elif direction == -1:
            idea.downvotes += 1
        idea.voters[voter_id] = direction
        self._reprice(idea)
        return idea

    def _reprice(self, idea: Idea) -> None:
        net = idea.upvotes - idea.downvotes
        idea.price = max(0.01, self.base_price * (1.0 + self.sensitivity * net))

    def trending(self, n: int = 5) -> list[Idea]:
        return sorted(self.ideas.values(), key=lambda i: i.price, reverse=True)[:n]

    def by_tag(self, tag: str) -> list[Idea]:
        return [i for i in self.ideas.values() if tag in i.tags]

    def by_author(self, author: str) -> list[Idea]:
        return [i for i in self.ideas.values() if i.author == author]

    def stats(self) -> dict:
        if not self.ideas:
            return {"ideas": 0, "avg_price": self.base_price}
        prices = [i.price for i in self.ideas.values()]
        return {
            "ideas": len(self.ideas),
            "avg_price": sum(prices) / len(prices),
            "max_price": max(prices),
            "min_price": min(prices),
            "total_votes": sum(i.upvotes + i.downvotes for i in self.ideas.values()),
        }
