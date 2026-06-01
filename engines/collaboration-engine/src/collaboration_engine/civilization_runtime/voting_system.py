"""Voting System — Handle voting on proposals"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


@dataclass
class Proposal:
    id: str = field(default_factory=lambda: f"PROP-{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    proposer: str = ""
    status: str = "open"
    votes: dict = field(default_factory=dict)
    deadline: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title, "status": self.status, "total_votes": len(self.votes)}


class VotingSystem:
    """Manage voting on proposals."""

    def __init__(self):
        self.proposals: dict[str, Proposal] = {}
        self.voting_history: list[dict] = []

    def vote(self, proposals: list[dict]) -> dict:
        """Process voting on proposals."""
        result = {"created": 0, "voted": 0}
        
        for prop_data in proposals:
            proposal = Proposal(
                title=prop_data.get("title", ""),
                description=prop_data.get("description", ""),
                proposer=prop_data.get("proposer", ""),
            )
            self.proposals[proposal.id] = proposal
            result["created"] += 1
        
        return result

    def cast_vote(self, proposal_id: str, voter_id: str, vote: str) -> bool:
        proposal = self.proposals.get(proposal_id)
        if not proposal or proposal.status != "open":
            return False
        
        proposal.votes[voter_id] = vote
        self.voting_history.append({
            "proposal_id": proposal_id,
            "voter_id": voter_id,
            "vote": vote,
            "timestamp": datetime.now().isoformat(),
        })
        return True

    def close_voting(self, proposal_id: str) -> dict:
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return {"error": "Proposal not found"}
        
        proposal.status = "closed"
        
        vote_counts = {}
        for vote in proposal.votes.values():
            vote_counts[vote] = vote_counts.get(vote, 0) + 1
        
        winner = max(vote_counts.items(), key=lambda x: x[1])[0] if vote_counts else None
        
        return {"proposal": proposal.to_dict(), "result": vote_counts, "winner": winner}

    def get_proposal_status(self, proposal_id: str) -> dict:
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return {"error": "Proposal not found"}
        return proposal.to_dict()

    def get_voting_stats(self) -> dict:
        return {
            "total_proposals": len(self.proposals),
            "open_proposals": sum(1 for p in self.proposals.values() if p.status == "open"),
            "total_votes_cast": len(self.voting_history),
        }