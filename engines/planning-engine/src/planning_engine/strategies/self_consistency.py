"""Self Consistency — Multiple reasoning paths with consistency voting"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable
from collections import Counter
import uuid


@dataclass
class ReasoningPath:
    id: str = field(default_factory=lambda: f"RP-{uuid.uuid4().hex[:8]}")
    steps: list[str] = field(default_factory=list)
    answer: str = ""
    confidence: float = 0.5
    reasoning: str = ""
    temperature: float = 0.7
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "steps": self.steps,
            "answer": self.answer,
            "confidence": self.confidence,
            "temperature": self.temperature,
        }


@dataclass
class ConsensusResult:
    question: str = ""
    paths: list[ReasoningPath] = field(default_factory=list)
    voted_answer: str = ""
    vote_count: int = 0
    agreement_ratio: float = 0.0
    confidence: float = 0.0
    is_consistent: bool = False

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "voted_answer": self.voted_answer,
            "vote_count": self.vote_count,
            "total_paths": len(self.paths),
            "agreement_ratio": f"{self.agreement_ratio:.0%}",
            "confidence": f"{self.confidence:.2f}",
            "is_consistent": self.is_consistent,
        }


class SelfConsistency:
    """Generate multiple reasoning paths and vote on consistent answers."""

    def __init__(self, reasoner: Optional[Callable] = None,
                 num_paths: int = 5,
                 temperature_range: tuple = (0.3, 1.0)):
        self.reasoner = reasoner or self._default_reasoner
        self.num_paths = num_paths
        self.temperature_range = temperature_range
        self.results: dict[str, ConsensusResult] = {}

    def solve(self, question: str, context: dict = None) -> ConsensusResult:
        result = ConsensusResult(question=question)
        temperatures = self._sample_temperatures()
        for temp in temperatures:
            path = self.reasoner(question, context or {}, temperature=temp)
            path.temperature = temp
            result.paths.append(path)

        # Vote on answers
        answer_counts = Counter(p.answer for p in result.paths)
        if answer_counts:
            voted_answer, vote_count = answer_counts.most_common(1)[0]
            result.voted_answer = voted_answer
            result.vote_count = vote_count
            result.agreement_ratio = vote_count / len(result.paths)
            result.confidence = self._calculate_confidence(result)
            result.is_consistent = result.agreement_ratio >= 0.6

        result_id = f"SC-{uuid.uuid4().hex[:8]}"
        self.results[result_id] = result
        return result

    def solve_with_verification(self, question: str, verifier: Callable,
                                context: dict = None) -> ConsensusResult:
        result = self.solve(question, context)
        for path in result.paths:
            is_valid = verifier(path.answer, question)
            path.metadata["verified"] = is_valid
            if not is_valid:
                path.confidence *= 0.5
        verified = [p for p in result.paths if p.metadata.get("verified")]
        if verified:
            verified_answers = Counter(p.answer for p in verified)
            voted_answer, vote_count = verified_answers.most_common(1)[0]
            result.voted_answer = voted_answer
            result.vote_count = vote_count
            result.agreement_ratio = vote_count / len(verified)
            result.confidence = self._calculate_confidence(result)
        return result

    def get_disagreements(self, result: ConsensusResult) -> list[dict]:
        answer_groups = {}
        for path in result.paths:
            if path.answer not in answer_groups:
                answer_groups[path.answer] = []
            answer_groups[path.answer].append(path)
        disagreements = []
        for answer, paths in answer_groups.items():
            if answer != result.voted_answer:
                disagreements.append({
                    "answer": answer,
                    "count": len(paths),
                    "paths": [p.id for p in paths],
                    "reasoning_samples": [p.reasoning[:100] for p in paths[:2]],
                })
        return disagreements

    def get_consistency_score(self, result: ConsensusResult) -> float:
        if not result.paths:
            return 0.0
        answer_counts = Counter(p.answer for p in result.paths)
        most_common_count = answer_counts.most_common(1)[0][1]
        return most_common_count / len(result.paths)

    def analyze_temperature_effect(self, results: list[ConsensusResult]) -> dict:
        temp_scores = []
        for result in results:
            for path in result.paths:
                temp_scores.append({
                    "temperature": path.temperature,
                    "confidence": path.confidence,
                    "correct": path.answer == result.voted_answer,
                })
        if not temp_scores:
            return {"analysis": "no data"}
        avg_by_temp = {}
        for ts in temp_scores:
            temp = round(ts["temperature"], 1)
            if temp not in avg_by_temp:
                avg_by_temp[temp] = {"confidences": [], "correct_count": 0, "total": 0}
            avg_by_temp[temp]["confidences"].append(ts["confidence"])
            avg_by_temp[temp]["total"] += 1
            if ts["correct"]:
                avg_by_temp[temp]["correct_count"] += 1
        analysis = {}
        for temp, data in avg_by_temp.items():
            analysis[str(temp)] = {
                "avg_confidence": sum(data["confidences"]) / len(data["confidences"]),
                "accuracy": data["correct_count"] / data["total"],
                "sample_count": data["total"],
            }
        return analysis

    def _sample_temperatures(self) -> list[float]:
        import random
        low, high = self.temperature_range
        return [low + (high - low) * i / (self.num_paths - 1)
                for i in range(self.num_paths)]

    def _calculate_confidence(self, result: ConsensusResult) -> float:
        if not result.paths:
            return 0.0
        agreement_bonus = result.agreement_ratio * 0.4
        path_confidences = [p.confidence for p in result.paths]
        avg_confidence = sum(path_confidences) / len(path_confidences)
        return min(1.0, avg_confidence * 0.6 + agreement_bonus)

    @staticmethod
    def _default_reasoner(question: str, context: dict, temperature: float = 0.7) -> ReasoningPath:
        import random
        random.seed(hash(question + str(temperature)))
        steps = [
            f"Step 1: Analyze the question (temp={temperature:.1f})",
            "Step 2: Consider relevant information",
            "Step 3: Formulate reasoning",
            "Step 4: Arrive at conclusion",
        ]
        answers = ["A", "B", "C", "D"]
        answer = random.choice(answers)
        return ReasoningPath(
            steps=steps,
            answer=answer,
            confidence=0.4 + random.random() * 0.4,
            reasoning=f"Reasoning at temperature {temperature:.1f}: the answer is {answer}",
            temperature=temperature,
        )
