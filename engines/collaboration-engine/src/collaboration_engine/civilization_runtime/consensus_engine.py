"""Consensus Engine — Reach consensus on proposals"""
from dataclasses import dataclass, field
from typing import Optional
import uuid
from datetime import datetime


@dataclass
class ConsensusProposal:
    id: str = field(default_factory=lambda: f"CON-{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    supporters: list[str] = field(default_factory=list)
    objectors: list[str] = field(default_factory=list)
    neutrals: list[str] = field(default_factory=list)
    status: str = "deliberation"
    consensus_level: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        total = len(self.supporters) + len(self.objectors) + len(self.neutrals)
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "consensus_level": round(self.consensus_level, 2),
            "total_participants": total,
        }


class ConsensusEngine:
    """Facilitate consensus-building processes."""

    def __init__(self):
        self.proposals: dict[str, ConsensusProposal] = {}
        self.consensus_threshold: float = 0.7

    def reach_consensus(self, proposals: list[dict]) -> dict:
        """Process proposals and work toward consensus."""
        result = {"processed": 0, "reached_consensus": 0}
        
        for prop_data in proposals:
            proposal = ConsensusProposal(
                title=prop_data.get("title", ""),
                description=prop_data.get("description", ""),
            )
            self.proposals[proposal.id] = proposal
            result["processed"] += 1
        
        return result

    def express_support(self, proposal_id: str, agent_id: str) -> bool:
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return False
        
        if agent_id in proposal.objectors:
            proposal.objectors.remove(agent_id)
        if agent_id in proposal.neutrals:
            proposal.neutrals.remove(agent_id)
        if agent_id not in proposal.supporters:
            proposal.supporters.append(agent_id)
        
        self._update_consensus_level(proposal)
        return True

    def express_objection(self, proposal_id: str, agent_id: str) -> bool:
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return False
        
        if agent_id in proposal.supporters:
            proposal.supporters.remove(agent_id)
        if agent_id in proposal.neutrals:
            proposal.neutrals.remove(agent_id)
        if agent_id not in proposal.objectors:
            proposal.objectors.append(agent_id)
        
        self._update_consensus_level(proposal)
        return True

    def remain_neutral(self, proposal_id: str, agent_id: str) -> bool:
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return False
        
        if agent_id in proposal.supporters:
            proposal.supporters.remove(agent_id)
        if agent_id in proposal.objectors:
            proposal.objectors.remove(agent_id)
        if agent_id not in proposal.neutrals:
            proposal.neutrals.append(agent_id)
        
        self._update_consensus_level(proposal)
        return True

    def _update_consensus_level(self, proposal: ConsensusProposal):
        total = len(proposal.supporters) + len(proposal.objectors) + len(proposal.neutrals)
        if total == 0:
            proposal.consensus_level = 0.0
        else:
            proposal.consensus_level = len(proposal.supporters) / total
        
        if proposal.consensus_level >= self.consensus_threshold:
            proposal.status = "consensus_reached"
        elif len(proposal.objectors) > len(proposal.supporters):
            proposal.status = "controversial"
        else:
            proposal.status = "deliberation"

    def get_consensus_status(self, proposal_id: str) -> dict:
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return {"error": "Proposal not found"}
        return proposal.to_dict()

    def get_consensus_stats(self) -> dict:
        proposals = list(self.proposals.values())
        return {
            "total_proposals": len(proposals),
            "consensus_reached": sum(1 for p in proposals if p.status == "consensus_reached"),
            "in_deliberation": sum(1 for p in proposals if p.status == "deliberation"),
            "controversial": sum(1 for p in proposals if p.status == "controversial"),
            "avg_consensus_level": sum(p.consensus_level for p in proposals) / len(proposals) if proposals else 0,
        }