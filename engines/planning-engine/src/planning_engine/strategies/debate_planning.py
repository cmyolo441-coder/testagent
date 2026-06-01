"""Debate Planning — Multi-agent debate for plan refinement"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable
import uuid


@dataclass
class DebatePosition:
    agent_id: str = ""
    position: str = ""
    arguments: list[str] = field(default_factory=list)
    confidence: float = 0.5
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "position": self.position,
            "arguments": self.arguments,
            "confidence": self.confidence,
            "evidence_count": len(self.evidence),
        }


@dataclass
class DebateRound:
    round_number: int = 1
    positions: list[DebatePosition] = field(default_factory=list)
    rebuttals: list[dict] = field(default_factory=list)
    synthesis: str = ""
    consensus_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "round": self.round_number,
            "positions": [p.to_dict() for p in self.positions],
            "rebuttals": self.rebuttals,
            "synthesis": self.synthesis,
            "consensus_score": f"{self.consensus_score:.0%}",
        }


@dataclass
class DebateSession:
    id: str = field(default_factory=lambda: f"DEB-{uuid.uuid4().hex[:8]}")
    topic: str = ""
    rounds: list[DebateRound] = field(default_factory=list)
    final_decision: str = ""
    confidence: float = 0.0
    agents: list[str] = field(default_factory=list)
    max_rounds: int = 3
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def round_count(self) -> int:
        return len(self.rounds)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "topic": self.topic,
            "rounds": [r.to_dict() for r in self.rounds],
            "final_decision": self.final_decision,
            "confidence": f"{self.confidence:.2f}",
            "agents": self.agents,
            "round_count": self.round_count,
        }


class DebatePlanning:
    """Multi-agent debate to refine plans through argumentation."""

    def __init__(self, agents: list[str] = None,
                 debate_fn: Optional[Callable] = None,
                 judge_fn: Optional[Callable] = None):
        self.agents = agents or ["agent_a", "agent_b", "agent_c"]
        self.debate_fn = debate_fn or self._default_debate
        self.judge_fn = judge_fn or self._default_judge
        self.sessions: dict[str, DebateSession] = {}

    def start_debate(self, topic: str, max_rounds: int = 3) -> DebateSession:
        session = DebateSession(topic=topic, agents=self.agents, max_rounds=max_rounds)
        self.sessions[session.id] = session
        # Round 1: Initial positions
        round_1 = self._conduct_round(session, 1)
        session.rounds.append(round_1)
        # Subsequent rounds: rebuttals
        for r in range(2, max_rounds + 1):
            prev_round = session.rounds[-1]
            round_n = self._conduct_round(session, r, prev_round)
            session.rounds.append(round_n)
            if self._has_consensus(round_n):
                break
        # Final decision
        session.final_decision = self._make_decision(session)
        session.confidence = self._calculate_confidence(session)
        return session

    def add_position(self, session_id: str, agent_id: str, position: str,
                     arguments: list[str] = None) -> bool:
        session = self.sessions.get(session_id)
        if not session:
            return False
        current_round = session.rounds[-1] if session.rounds else DebateRound()
        if not session.rounds:
            session.rounds.append(current_round)
        pos = DebatePosition(
            agent_id=agent_id,
            position=position,
            arguments=arguments or [],
        )
        current_round.positions.append(pos)
        return True

    def add_rebuttal(self, session_id: str, target_agent: str,
                     rebuttal: str, from_agent: str) -> bool:
        session = self.sessions.get(session_id)
        if not session or not session.rounds:
            return False
        current_round = session.rounds[-1]
        current_round.rebuttals.append({
            "from": from_agent,
            "to": target_agent,
            "rebuttal": rebuttal,
        })
        return True

    def get_debate_summary(self, session_id: str) -> dict:
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "session not found"}
        all_positions = []
        for round in session.rounds:
            all_positions.extend(round.positions)
        position_counts = {}
        for pos in all_positions:
            position_counts[pos.position] = position_counts.get(pos.position, 0) + 1
        return {
            "id": session.id,
            "topic": session.topic,
            "rounds": session.round_count,
            "agents": len(session.agents),
            "positions_taken": len(all_positions),
            "unique_positions": len(position_counts),
            "most_common": max(position_counts.items(), key=lambda x: x[1])[0] if position_counts else "",
            "final_decision": session.final_decision,
            "confidence": f"{session.confidence:.0%}",
        }

    def vote(self, session_id: str) -> dict:
        session = self.sessions.get(session_id)
        if not session or not session.rounds:
            return {"error": "no session"}
        last_round = session.rounds[-1]
        votes = {}
        for pos in last_round.positions:
            votes[pos.agent_id] = pos.position
        from collections import Counter
        vote_counts = Counter(votes.values())
        winner, win_count = vote_counts.most_common(1)[0]
        return {
            "votes": votes,
            "winner": winner,
            "vote_count": win_count,
            "total_votes": len(votes),
        }

    def _conduct_round(self, session: DebateSession, round_num: int,
                       prev_round: DebateRound = None) -> DebateRound:
        round_obj = DebateRound(round_number=round_num)
        for agent in session.agents:
            position = self.debate_fn(session.topic, agent, prev_round)
            round_obj.positions.append(position)
        if prev_round:
            for pos in round_obj.positions:
                targets = [p for p in prev_round.positions if p.agent_id != pos.agent_id]
                for target in targets[:1]:
                    rebuttal = f"Rebuttal from {pos.agent_id}: challenging {target.agent_id}'s position"
                    round_obj.rebuttals.append({
                        "from": pos.agent_id,
                        "to": target.agent_id,
                        "rebuttal": rebuttal,
                    })
        round_obj.consensus_score = self._calculate_round_consensus(round_obj)
        return round_obj

    def _has_consensus(self, round_obj: DebateRound) -> bool:
        return round_obj.consensus_score >= 0.8

    def _make_decision(self, session: DebateSession) -> str:
        if not session.rounds:
            return "No decision"
        last_round = session.rounds[-1]
        if last_round.positions:
            best = max(last_round.positions, key=lambda p: p.confidence)
            return best.position
        return "No consensus"

    def _calculate_confidence(self, session: DebateSession) -> float:
        if not session.rounds:
            return 0.0
        last_round = session.rounds[-1]
        if not last_round.positions:
            return 0.0
        return last_round.consensus_score

    def _calculate_round_consensus(self, round_obj: DebateRound) -> float:
        if not round_obj.positions:
            return 0.0
        positions = [p.position for p in round_obj.positions]
        from collections import Counter
        counts = Counter(positions)
        most_common_count = counts.most_common(1)[0][1]
        return most_common_count / len(positions)

    @staticmethod
    def _default_debate(topic: str, agent_id: str, prev_round: DebateRound = None) -> DebatePosition:
        return DebatePosition(
            agent_id=agent_id,
            position=f"Position from {agent_id} on: {topic[:50]}",
            arguments=[f"Argument 1 from {agent_id}", f"Argument 2 from {agent_id}"],
            confidence=0.5 + hash(agent_id + topic) % 100 / 200,
        )

    @staticmethod
    def _default_judge(positions: list[DebatePosition], topic: str) -> str:
        if not positions:
            return "No decision"
        return max(positions, key=lambda p: p.confidence).position
