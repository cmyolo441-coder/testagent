"""Peer Review System — Submit work, assign reviewers, aggregate verdicts."""
from dataclasses import dataclass, field
from typing import Optional
import random
import time
import uuid


@dataclass
class ReviewSubmission:
    work_id: str
    author_id: str
    content: str
    submitted_at: float = field(default_factory=time.time)
    assigned_reviewers: list[str] = field(default_factory=list)
    reviews: dict[str, "Review"] = field(default_factory=dict)


@dataclass
class Review:
    work_id: str
    reviewer_id: str
    score: float
    comments: str = ""
    ts: float = field(default_factory=time.time)


@dataclass
class ReviewVerdict:
    work_id: str
    avg_score: float
    passed: bool
    dissent_count: int
    review_count: int
    rationale: str = ""


class PeerReviewSystem:
    """Manage peer review lifecycle: submit, assign, collect, aggregate."""

    def __init__(self, reviewer_pool: Optional[list[str]] = None, pass_threshold: float = 0.6):
        self.reviewer_pool: list[str] = list(reviewer_pool or [])
        self.pass_threshold = pass_threshold
        self.submissions: dict[str, ReviewSubmission] = {}

    def register_reviewer(self, reviewer_id: str) -> None:
        if reviewer_id not in self.reviewer_pool:
            self.reviewer_pool.append(reviewer_id)

    def submit_for_review(self, work_id: str, author_id: str, content: str) -> ReviewSubmission:
        if not work_id:
            work_id = f"WORK-{uuid.uuid4().hex[:8]}"
        submission = ReviewSubmission(work_id=work_id, author_id=author_id, content=content)
        self.submissions[work_id] = submission
        return submission

    def assign_reviewers(self, work_id: str, n: int = 3) -> list[str]:
        submission = self.submissions.get(work_id)
        if not submission:
            raise KeyError(f"Unknown work_id: {work_id}")
        candidates = [r for r in self.reviewer_pool if r != submission.author_id]
        n = min(n, len(candidates))
        chosen = random.sample(candidates, n) if n > 0 else []
        submission.assigned_reviewers = chosen
        return chosen

    def collect_review(self, work_id: str, reviewer_id: str, score: float, comments: str = "") -> Review:
        submission = self.submissions.get(work_id)
        if not submission:
            raise KeyError(f"Unknown work_id: {work_id}")
        score = max(0.0, min(1.0, score))
        review = Review(work_id=work_id, reviewer_id=reviewer_id, score=score, comments=comments)
        submission.reviews[reviewer_id] = review
        return review

    def aggregate(self, work_id: str) -> ReviewVerdict:
        submission = self.submissions.get(work_id)
        if not submission:
            raise KeyError(f"Unknown work_id: {work_id}")
        reviews = list(submission.reviews.values())
        if not reviews:
            return ReviewVerdict(
                work_id=work_id,
                avg_score=0.0,
                passed=False,
                dissent_count=0,
                review_count=0,
                rationale="no reviews collected",
            )
        avg = sum(r.score for r in reviews) / len(reviews)
        passed = avg >= self.pass_threshold
        dissent = sum(1 for r in reviews if (r.score >= self.pass_threshold) != passed)
        return ReviewVerdict(
            work_id=work_id,
            avg_score=avg,
            passed=passed,
            dissent_count=dissent,
            review_count=len(reviews),
            rationale=f"avg={avg:.3f} threshold={self.pass_threshold}",
        )

    def get_pending(self) -> list[ReviewSubmission]:
        return [s for s in self.submissions.values()
                if len(s.reviews) < len(s.assigned_reviewers)]
