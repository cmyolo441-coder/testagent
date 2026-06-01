"""Feedback Collector — Collect and summarize user feedback records."""
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime, timezone
import uuid
import json


@dataclass
class FeedbackRecord:
    id: str = field(default_factory=lambda: f"FB-{uuid.uuid4().hex[:8]}")
    target_type: str = "action"  # action, answer, plan
    target_id: str = ""
    rating: float = 0.0  # -1.0 .. +1.0
    reason: Optional[str] = None
    user_id: Optional[str] = None
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FeedbackCollector:
    """Collects FeedbackRecord items and aggregates by target_type."""

    VALID_TYPES = ("action", "answer", "plan")

    def __init__(self):
        self.records: list[FeedbackRecord] = []
        self.buckets: dict[str, list[FeedbackRecord]] = {t: [] for t in self.VALID_TYPES}

    def collect(
        self,
        target_type: str,
        target_id: str,
        rating: float,
        reason: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> FeedbackRecord:
        if target_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid target_type: {target_type}")
        rating = max(-1.0, min(1.0, float(rating)))
        record = FeedbackRecord(
            target_type=target_type,
            target_id=target_id,
            rating=rating,
            reason=reason,
            user_id=user_id,
        )
        self.records.append(record)
        self.buckets.setdefault(target_type, []).append(record)
        return record

    def summarize(self, target_type: Optional[str] = None) -> dict:
        if target_type is not None:
            bucket = self.buckets.get(target_type, [])
            return self._summarize_bucket(target_type, bucket)
        return {
            t: self._summarize_bucket(t, recs)
            for t, recs in self.buckets.items()
        }

    def _summarize_bucket(self, name: str, bucket: list[FeedbackRecord]) -> dict:
        count = len(bucket)
        avg = sum(r.rating for r in bucket) / count if count else 0.0
        return {
            "target_type": name,
            "count": count,
            "avg_rating": avg,
            "positive": sum(1 for r in bucket if r.rating > 0),
            "negative": sum(1 for r in bucket if r.rating < 0),
            "neutral": sum(1 for r in bucket if r.rating == 0),
        }

    def export_jsonl(self, path: str) -> int:
        with open(path, "w", encoding="utf-8") as f:
            for record in self.records:
                f.write(json.dumps(asdict(record)) + "\n")
        return len(self.records)

    def to_dict(self) -> dict:
        return {
            "total": len(self.records),
            "buckets": {t: len(b) for t, b in self.buckets.items()},
            "summary": self.summarize(),
        }
