"""Peer Review Orchestrator - Manages peer review of scientific work."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


ORCHESTRATOR_VERSION = "2.0"


class ReviewDecision(Enum):
    """Possible review decisions."""
    ACCEPT = "accept"
    ACCEPT_WITH_MINOR_REVISIONS = "accept_with_minor_revisions"
    MAJOR_REVISIONS_REQUIRED = "major_revisions_required"
    REJECT_AND_RESUBMIT = "reject_and_resubmit"
    REJECT = "reject"


class ReviewerExpertise(Enum):
    """Reviewer expertise level."""
    EXPERT = "expert"
    KNOWLEDGEABLE = "knowledgeable"
    SOME_KNOWLEDGE = "some_knowledge"
    NOVICE = "novice"


@dataclass
class ReviewCriteria:
    """Criteria for evaluating scientific work."""
    originality: float
    methodology: float
    significance: float
    clarity: float
    validity: float
    reproducibility: float
    literature_review: float
    
    @property
    def overall_score(self) -> float:
        return (
            self.originality * 0.15
            + self.methodology * 0.25
            + self.significance * 0.20
            + self.clarity * 0.10
            + self.validity * 0.20
            + self.reproducibility * 0.05
            + self.literature_review * 0.05
        )


@dataclass
class ReviewComment:
    """A single review comment."""
    category: str
    severity: str
    text: str
    suggestion: Optional[str]


@dataclass
class PeerReview:
    """Complete peer review."""
    reviewer_id: str
    reviewer_expertise: ReviewerExpertise
    decision: ReviewDecision
    criteria: ReviewCriteria
    comments: List[ReviewComment]
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "reviewer_id": self.reviewer_id,
            "reviewer_expertise": self.reviewer_expertise.value,
            "decision": self.decision.value,
            "criteria": {
                "originality": self.criteria.originality,
                "methodology": self.criteria.methodology,
                "significance": self.criteria.significance,
                "clarity": self.criteria.clarity,
                "validity": self.criteria.validity,
                "reproducibility": self.criteria.reproducibility,
                "literature_review": self.criteria.literature_review,
                "overall_score": self.criteria.overall_score,
            },
            "comments": [{"category": c.category, "severity": c.severity, 
                          "text": c.text, "suggestion": c.suggestion} for c in self.comments],
            "summary": self.summary,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendations": self.recommendations,
        }


@dataclass
class PeerReviewResults:
    """Aggregated results from multiple peer reviews."""
    work_id: str
    reviews: List[PeerReview]
    aggregate_decision: ReviewDecision
    average_score: float
    consensus_level: float
    major_issues: List[str]
    minor_issues: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "work_id": self.work_id,
            "reviews": [r.to_dict() for r in self.reviews],
            "aggregate_decision": self.aggregate_decision.value,
            "average_score": self.average_score,
            "consensus_level": self.consensus_level,
            "major_issues": self.major_issues,
            "minor_issues": self.minor_issues,
        }


class PeerReviewOrchestrator:
    """Manages peer review of scientific work.
    
    Orchestrates the peer review process, collecting and aggregating
    reviews from multiple reviewers.
    """
    
    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._reviews: Dict[str, PeerReviewResults] = {}
        self._counter = 0
    
    def orchestrate(self, work: Dict[str, Any], num_reviewers: int = 3) -> PeerReviewResults:
        """Orchestrate heuristic peer review of scientific work.

        Args:
            work: Scientific work to review
            num_reviewers: Number of heuristic reviewer agents

        Returns:
            PeerReviewResults with aggregated reviews
        """
        return self._run(work, num_reviewers, self._generate_review)

    def orchestrate_with_callback(
        self,
        work: Dict[str, Any],
        num_reviewers: int,
        review_fn: Callable[[Dict[str, Any], ReviewerExpertise], PeerReview],
    ) -> PeerReviewResults:
        """Orchestrate peer review using a pluggable reviewer callable.

        Args:
            work: Scientific work to review
            num_reviewers: Number of reviewer agents
            review_fn: Callable ``(work, expertise) -> PeerReview`` that
                replaces the default heuristic reviewer for this call. This
                allows external real-LLM (or other) reviewers to be plugged
                in without altering the orchestrator's aggregation logic.

        Returns:
            PeerReviewResults with aggregated reviews
        """
        def _adapter(work_arg, expertise, _idx):
            return review_fn(work_arg, expertise)

        return self._run(work, num_reviewers, _adapter)

    def _run(
        self,
        work: Dict[str, Any],
        num_reviewers: int,
        review_callable: Callable[[Dict[str, Any], ReviewerExpertise, int], PeerReview],
    ) -> PeerReviewResults:
        """Shared orchestration pipeline used by orchestrate variants."""
        self._counter += 1

        work_id = work.get("id", "unknown")
        work_type = work.get("type", "paper")

        # Generate reviews from reviewer agents
        reviews = []
        for i in range(num_reviewers):
            reviewer_expertise = self._rng.choice(list(ReviewerExpertise))
            review = review_callable(work, reviewer_expertise, i)
            reviews.append(review)

        # Aggregate reviews
        aggregate_decision = self._aggregate_decisions(reviews)
        average_score = self._calculate_average_score(reviews)
        consensus_level = self._calculate_consensus(reviews)
        major_issues = self._collect_major_issues(reviews)
        minor_issues = self._collect_minor_issues(reviews)

        results = PeerReviewResults(
            work_id=work_id,
            reviews=reviews,
            aggregate_decision=aggregate_decision,
            average_score=average_score,
            consensus_level=consensus_level,
            major_issues=major_issues,
            minor_issues=minor_issues,
        )

        self._reviews[work_id] = results
        return results

    def _generate_review(
        self, work: Dict[str, Any], expertise: ReviewerExpertise, reviewer_idx: int
    ) -> PeerReview:
        """Generate a heuristic (rule-based) review."""
        # Score based on expertise
        expertise_factor = {
            ReviewerExpertise.EXPERT: 1.0,
            ReviewerExpertise.KNOWLEDGEABLE: 0.9,
            ReviewerExpertise.SOME_KNOWLEDGE: 0.75,
            ReviewerExpertise.NOVICE: 0.6,
        }[expertise]
        
        # Generate scores with some randomness
        base_score = 0.6 + self._rng.uniform(-0.2, 0.2)
        
        criteria = ReviewCriteria(
            originality=min(max(base_score + self._rng.uniform(-0.1, 0.1), 0), 1),
            methodology=min(max(base_score + self._rng.uniform(-0.1, 0.1), 0), 1),
            significance=min(max(base_score + self._rng.uniform(-0.1, 0.1), 0), 1),
            clarity=min(max(base_score + self._rng.uniform(-0.1, 0.1), 0), 1),
            validity=min(max(base_score + self._rng.uniform(-0.1, 0.1), 0), 1),
            reproducibility=min(max(base_score + self._rng.uniform(-0.1, 0.1), 0), 1),
            literature_review=min(max(base_score + self._rng.uniform(-0.1, 0.1), 0), 1),
        )
        
        # Determine decision
        decision = self._score_to_decision(criteria.overall_score)
        
        # Generate comments
        comments = self._generate_comments(criteria, work)
        
        # Generate strengths and weaknesses
        strengths = self._identify_strengths(criteria, work)
        weaknesses = self._identify_weaknesses(criteria, work)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(decision, weaknesses)
        
        # Generate summary
        summary = self._generate_summary(decision, criteria)
        
        reviewer_id = f"Reviewer_{reviewer_idx + 1}"
        
        return PeerReview(
            reviewer_id=reviewer_id,
            reviewer_expertise=expertise,
            decision=decision,
            criteria=criteria,
            comments=comments,
            summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
        )
    
    def _score_to_decision(self, score: float) -> ReviewDecision:
        """Convert numerical score to decision."""
        if score >= 0.85:
            return ReviewDecision.ACCEPT
        elif score >= 0.7:
            return ReviewDecision.ACCEPT_WITH_MINOR_REVISIONS
        elif score >= 0.5:
            return ReviewDecision.MAJOR_REVISIONS_REQUIRED
        elif score >= 0.3:
            return ReviewDecision.REJECT_AND_RESUBMIT
        else:
            return ReviewDecision.REJECT
    
    def _generate_comments(
        self, criteria: ReviewCriteria, work: Dict[str, Any]
    ) -> List[ReviewComment]:
        """Generate review comments."""
        comments = []
        
        if criteria.methodology < 0.5:
            comments.append(ReviewComment(
                category="Methodology",
                severity="major",
                text="Methodology has significant limitations that need to be addressed",
                suggestion="Consider additional controls and validation procedures",
            ))
        
        if criteria.clarity < 0.6:
            comments.append(ReviewComment(
                category="Clarity",
                severity="minor",
                text="Writing could be clearer in several sections",
                suggestion="Revise for clarity and add more detailed explanations",
            ))
        
        if criteria.originality < 0.4:
            comments.append(ReviewComment(
                category="Originality",
                severity="major",
                text="Limited novelty compared to existing literature",
                suggestion="Better position work relative to prior art",
            ))
        
        # Add positive comments
        if criteria.significance > 0.7:
            comments.append(ReviewComment(
                category="Significance",
                severity="positive",
                text="Addresses an important research question",
                suggestion=None,
            ))
        
        return comments
    
    def _identify_strengths(
        self, criteria: ReviewCriteria, work: Dict[str, Any]
    ) -> List[str]:
        """Identify strengths of the work."""
        strengths = []
        
        if criteria.originality > 0.7:
            strengths.append("Novel approach to the research question")
        
        if criteria.methodology > 0.7:
            strengths.append("Sound methodology and experimental design")
        
        if criteria.significance > 0.7:
            strengths.append("Addresses an important and timely research question")
        
        if criteria.validity > 0.7:
            strengths.append("Results appear valid and well-supported")
        
        if criteria.clarity > 0.7:
            strengths.append("Clear and well-organized presentation")
        
        if not strengths:
            strengths.append("Contributes to the existing body of knowledge")
        
        return strengths[:4]
    
    def _identify_weaknesses(
        self, criteria: ReviewCriteria, work: Dict[str, Any]
    ) -> List[str]:
        """Identify weaknesses of the work."""
        weaknesses = []
        
        if criteria.methodology < 0.6:
            weaknesses.append("Methodological concerns need to be addressed")
        
        if criteria.clarity < 0.6:
            weaknesses.append("Clarity of presentation needs improvement")
        
        if criteria.originality < 0.5:
            weaknesses.append("Limited novelty relative to existing work")
        
        if criteria.reproducibility < 0.5:
            weaknesses.append("Insufficient detail for replication")
        
        if criteria.literature_review < 0.5:
            weaknesses.append("Literature review does not adequately cover prior work")
        
        return weaknesses[:4]
    
    def _generate_recommendations(
        self, decision: ReviewDecision, weaknesses: List[str]
    ) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        if decision in [ReviewDecision.ACCEPT_WITH_MINOR_REVISIONS, 
                       ReviewDecision.MAJOR_REVISIONS_REQUIRED]:
            recommendations.append("Address all reviewer comments systematically")
            recommendations.append("Provide point-by-point responses to reviewer concerns")
        
        if decision == ReviewDecision.REJECT_AND_RESUBMIT:
            recommendations.append("Consider fundamental revisions to methodology")
            recommendations.append("Seek additional feedback before resubmission")
        
        if any("methodology" in w.lower() for w in weaknesses):
            recommendations.append("Strengthen experimental design and controls")
        
        if any("clarity" in w.lower() for w in weaknesses):
            recommendations.append("Improve clarity of writing and figure quality")
        
        recommendations.append("Ensure all claims are properly supported by evidence")
        
        return recommendations[:4]
    
    def _generate_summary(self, decision: ReviewDecision, criteria: ReviewCriteria) -> str:
        """Generate review summary."""
        score = criteria.overall_score
        
        summary = f"Overall assessment: {decision.value.replace('_', ' ')}. "
        summary += f"Score: {score:.2f}/1.00. "
        
        if score >= 0.7:
            summary += "The work makes a solid contribution but may benefit from minor improvements."
        elif score >= 0.5:
            summary += "The work has merit but requires significant revisions before publication."
        else:
            summary += "Major concerns need to be addressed before the work can be considered for publication."
        
        return summary
    
    def _aggregate_decisions(self, reviews: List[PeerReview]) -> ReviewDecision:
        """Aggregate decisions from multiple reviews."""
        decisions = [r.decision for r in reviews]
        
        # Count each decision type
        decision_counts = {}
        for d in decisions:
            decision_counts[d] = decision_counts.get(d, 0) + 1
        
        # Weight by reviewer expertise
        weighted_counts = {}
        for review in reviews:
            expertise_weight = {
                ReviewerExpertise.EXPERT: 1.5,
                ReviewerExpertise.KNOWLEDGEABLE: 1.2,
                ReviewerExpertise.SOME_KNOWLEDGE: 1.0,
                ReviewerExpertise.NOVICE: 0.8,
            }[review.reviewer_expertise]
            
            weighted_counts[review.decision] = (
                weighted_counts.get(review.decision, 0) + expertise_weight
            )
        
        # Return weighted majority decision
        return max(weighted_counts, key=weighted_counts.get)
    
    def _calculate_average_score(self, reviews: List[PeerReview]) -> float:
        """Calculate average score across reviews."""
        scores = [r.criteria.overall_score for r in reviews]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_consensus(self, reviews: List[PeerReview]) -> float:
        """Calculate consensus level among reviewers."""
        decisions = [r.decision for r in reviews]
        
        if len(decisions) < 2:
            return 1.0
        
        most_common = max(set(decisions), key=decisions.count)
        agreement_ratio = decisions.count(most_common) / len(decisions)
        
        return round(agreement_ratio, 3)
    
    def _collect_major_issues(self, reviews: List[PeerReview]) -> List[str]:
        """Collect major issues from all reviews."""
        issues = []
        
        for review in reviews:
            for comment in review.comments:
                if comment.severity == "major":
                    issues.append(comment.text)
        
        return list(dict.fromkeys(issues))[:5]
    
    def _collect_minor_issues(self, reviews: List[PeerReview]) -> List[str]:
        """Collect minor issues from all reviews."""
        issues = []
        
        for review in reviews:
            for comment in review.comments:
                if comment.severity == "minor":
                    issues.append(comment.text)
        
        return list(dict.fromkeys(issues))[:5]
