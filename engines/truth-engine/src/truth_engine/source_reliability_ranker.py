"""Source Reliability Ranker — score sources for reliability based on type,
known reputation tier and recency.
"""
from dataclasses import dataclass
from datetime import datetime, timezone


# Coarse domain-tier table — extended over time, evidence-driven not gospel
DOMAIN_TIER = {
    # tier 1 — peer-reviewed / primary
    "nature.com": 0.95, "science.org": 0.95, "cell.com": 0.92,
    "arxiv.org": 0.75,  # preprint, no peer review
    "pubmed.ncbi.nlm.nih.gov": 0.92,
    # tier 2 — high-quality reference
    "wikipedia.org": 0.7,
    "doi.org": 0.85,
    # tier 3 — institutional
    "nasa.gov": 0.9, "nih.gov": 0.9, "cdc.gov": 0.85,
    # tier 4 — established press
    "reuters.com": 0.8, "apnews.com": 0.8, "bbc.com": 0.75,
    "nytimes.com": 0.7, "washingtonpost.com": 0.7,
    # tier 5 — blogs/forums
    "medium.com": 0.4, "reddit.com": 0.3,
}

TYPE_PRIOR = {
    "peer_reviewed": 0.9, "preprint": 0.7, "official_report": 0.85,
    "press": 0.6, "blog": 0.4, "forum": 0.3, "social": 0.2,
    "primary_source": 0.85, "secondary": 0.65, "tertiary": 0.55,
}


@dataclass
class SourceScore:
    url_or_id: str
    score: float
    tier_reason: str
    age_days: int
    decay_factor: float


class SourceReliabilityRanker:
    def __init__(self, half_life_days: int = 365 * 3):
        self.half_life = half_life_days

    def score(self, url_or_id: str, source_type: str = "secondary",
              published_at: str | None = None) -> SourceScore:
        base = TYPE_PRIOR.get(source_type, 0.5)
        tier_reason = f"type-prior={source_type}({base:.2f})"

        for domain, dscore in DOMAIN_TIER.items():
            if domain in url_or_id:
                base = max(base, dscore)
                tier_reason = f"domain-match {domain} → {dscore:.2f}"
                break

        decay = 1.0
        age = 0
        if published_at:
            try:
                pub = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - pub).days
                decay = 0.5 ** (age / self.half_life)
            except Exception:
                pass

        return SourceScore(
            url_or_id=url_or_id,
            score=round(min(1.0, base * decay), 3),
            tier_reason=tier_reason,
            age_days=age,
            decay_factor=round(decay, 3),
        )

    def rank(self, sources: list[dict]) -> list[SourceScore]:
        out = [self.score(s["url"], s.get("type", "secondary"), s.get("published_at"))
               for s in sources]
        return sorted(out, key=lambda x: x.score, reverse=True)
