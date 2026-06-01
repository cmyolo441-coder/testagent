"""Cost Tracker — Per-user / per-mission / per-model USD spend ledger."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Optional

from llm_gateway.routing.model_router import ModelRouter


@dataclass
class CostEntry:
    ts: str
    model: str
    in_tok: int
    out_tok: int
    cost: float
    user_id: Optional[str] = None
    mission_id: Optional[str] = None


class CostTracker:
    """In-memory cost ledger with budget enforcement, window summaries, JSONL export."""

    def __init__(self):
        self.entries: list[CostEntry] = []
        self._models = ModelRouter.MODELS

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------
    def record(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        user_id: Optional[str] = None,
        mission_id: Optional[str] = None,
    ) -> CostEntry:
        info = self._models.get(model)
        if info is None:
            cost = 0.0
        else:
            cost = (
                (input_tokens / 1000.0) * info.cost_per_1k_input
                + (output_tokens / 1000.0) * info.cost_per_1k_output
            )
        entry = CostEntry(
            ts=datetime.now(timezone.utc).isoformat(),
            model=model,
            in_tok=int(input_tokens),
            out_tok=int(output_tokens),
            cost=round(float(cost), 8),
            user_id=user_id,
            mission_id=mission_id,
        )
        self.entries.append(entry)
        return entry

    # ------------------------------------------------------------------
    # Budget enforcement
    # ------------------------------------------------------------------
    def enforce_budget(
        self, user_id: str, max_usd: float, window: str = "month"
    ) -> bool:
        """Return True while ``user_id`` is within ``max_usd`` for ``window``."""
        cutoff = self._window_cutoff(window)
        total = 0.0
        for e in self.entries:
            if e.user_id != user_id:
                continue
            if cutoff and self._parse_ts(e.ts) < cutoff:
                continue
            total += e.cost
        return total <= float(max_usd)

    # ------------------------------------------------------------------
    # Summarization
    # ------------------------------------------------------------------
    def summarize(
        self, window: str = "all", user_id: Optional[str] = None
    ) -> dict:
        cutoff = self._window_cutoff(window)
        per_model: dict[str, float] = defaultdict(float)
        per_user: dict[str, float] = defaultdict(float)
        total = 0.0
        count = 0
        for e in self.entries:
            if cutoff and self._parse_ts(e.ts) < cutoff:
                continue
            if user_id is not None and e.user_id != user_id:
                continue
            total += e.cost
            count += 1
            per_model[e.model] += e.cost
            if e.user_id:
                per_user[e.user_id] += e.cost
        return {
            "total_cost": round(total, 6),
            "per_model": {k: round(v, 6) for k, v in per_model.items()},
            "per_user": {k: round(v, 6) for k, v in per_user.items()},
            "count": count,
        }

    def top_spenders(self, n: int = 5) -> list[tuple[str, float]]:
        totals: dict[str, float] = defaultdict(float)
        for e in self.entries:
            if e.user_id:
                totals[e.user_id] += e.cost
        ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
        return [(uid, round(c, 6)) for uid, c in ranked[:n]]

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def export_jsonl(self, path: str) -> int:
        with open(path, "w", encoding="utf-8") as f:
            for e in self.entries:
                f.write(json.dumps(asdict(e), separators=(",", ":")) + "\n")
        return len(self.entries)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_ts(ts: str) -> datetime:
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            return datetime.now(timezone.utc)

    @staticmethod
    def _window_cutoff(window: str) -> Optional[datetime]:
        now = datetime.now(timezone.utc)
        if window == "day":
            return now - timedelta(days=1)
        if window == "month":
            return now - timedelta(days=30)
        if window == "week":
            return now - timedelta(days=7)
        if window == "hour":
            return now - timedelta(hours=1)
        return None
