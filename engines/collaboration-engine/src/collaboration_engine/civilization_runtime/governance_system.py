"""Governance System — Make governance decisions"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class DecisionType(Enum):
    POLICY = "policy"
    RESOURCE = "resource"
    PERSONNEL = "personnel"
    STRATEGIC = "strategic"
    EMERGENCY = "emergency"


@dataclass
class GovernanceDecision:
    id: str = field(default_factory=lambda: f"GOV-{uuid.uuid4().hex[:8]}")
    title: str = ""
    decision_type: DecisionType = DecisionType.POLICY
    description: str = ""
    proposer: str = ""
    voters: list[str] = field(default_factory=list)
    votes_for: int = 0
    votes_against: int = 0
    abstentions: int = 0
    status: str = "pending"
    implementation_date: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "type": self.decision_type.value,
            "status": self.status,
            "votes_for": self.votes_for,
            "votes_against": self.votes_against,
        }


class GovernanceSystem:
    """Manage governance decisions and processes."""

    def __init__(self):
        self.decisions: dict[str, GovernanceDecision] = {}
        self.policies: list[dict] = []
        self.committees: dict[str, list[str]] = {}

    def govern(self, decisions: list[dict]) -> dict:
        """Process governance decisions."""
        result = {"processed": 0, "approved": 0, "rejected": 0}
        
        for decision_data in decisions:
            decision = GovernanceDecision(
                title=decision_data.get("title", ""),
                description=decision_data.get("description", ""),
                proposer=decision_data.get("proposer", ""),
                decision_type=DecisionType(decision_data.get("type", "policy")),
            )
            
            self.decisions[decision.id] = decision
            result["processed"] += 1
        
        return result

    def vote(self, decision_id: str, voter_id: str, vote: str) -> bool:
        """Cast a vote on a decision."""
        decision = self.decisions.get(decision_id)
        if not decision or voter_id in decision.voters:
            return False
        
        decision.voters.append(voter_id)
        
        if vote.lower() == "for":
            decision.votes_for += 1
        elif vote.lower() == "against":
            decision.votes_against += 1
        elif vote.lower() == "abstain":
            decision.abstentions += 1
        
        self._check_decision_outcome(decision)
        return True

    def _check_decision_outcome(self, decision: GovernanceDecision):
        """Check if a decision has reached a quorum and determine outcome."""
        total_votes = decision.votes_for + decision.votes_against + decision.abstentions
        
        if total_votes >= 3:  # Minimum quorum
            if decision.votes_for > decision.votes_against:
                decision.status = "approved"
            else:
                decision.status = "rejected"

    def get_pending_decisions(self) -> list[dict]:
        return [d.to_dict() for d in self.decisions.values() if d.status == "pending"]

    def get_decision_history(self) -> list[dict]:
        return [d.to_dict() for d in self.decisions.values() if d.status in ["approved", "rejected"]]

    def create_policy(self, title: str, description: str, category: str) -> dict:
        policy = {
            "id": f"POL-{uuid.uuid4().hex[:8]}",
            "title": title,
            "description": description,
            "category": category,
            "status": "active",
            "created_at": datetime.now().isoformat(),
        }
        self.policies.append(policy)
        return policy

    def get_governance_stats(self) -> dict:
        decisions = list(self.decisions.values())
        return {
            "total_decisions": len(decisions),
            "pending": sum(1 for d in decisions if d.status == "pending"),
            "approved": sum(1 for d in decisions if d.status == "approved"),
            "rejected": sum(1 for d in decisions if d.status == "rejected"),
            "policies_count": len(self.policies),
        }