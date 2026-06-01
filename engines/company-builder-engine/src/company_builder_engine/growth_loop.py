"""Growth Loop — Design growth strategies"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


@dataclass
class GrowthExperiment:
    id: str = field(default_factory=lambda: f"GEXP-{uuid.uuid4().hex[:8]}")
    name: str = ""
    hypothesis: str = ""
    channel: str = ""
    metric: str = ""
    current_value: float = 0
    target_value: float = 0
    status: str = "planned"
    results: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "channel": self.channel, "metric": self.metric, "status": self.status}


@dataclass
class GrowthStrategy:
    id: str = field(default_factory=lambda: f"GSTRAT-{uuid.uuid4().hex[:8]}")
    channels: list[str] = field(default_factory=list)
    experiments: list[GrowthExperiment] = field(default_factory=list)
    funnel: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    strategies: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {"id": self.id, "channels": self.channels, "experiments_count": len(self.experiments)}


class GrowthLoop:
    """Design and manage growth strategies."""

    def __init__(self):
        self.strategies: dict[str, GrowthStrategy] = {}
        self.experiments: dict[str, GrowthExperiment] = {}

    def design(self, metrics: dict) -> GrowthStrategy:
        """Design growth strategy based on metrics."""
        strategy = GrowthStrategy()
        
        strategy.channels = self._identify_channels(metrics)
        strategy.experiments = self._create_experiments(strategy.channels, metrics)
        for exp in strategy.experiments:
            self.experiments[exp.id] = exp
        
        strategy.funnel = self._design_funnel(metrics)
        strategy.metrics = self._define_growth_metrics(metrics)
        strategy.strategies = self._define_strategies(metrics)
        
        self.strategies[strategy.id] = strategy
        return strategy

    def _identify_channels(self, metrics: dict) -> list[str]:
        user_count = metrics.get("users", 0)
        if user_count < 1000:
            return ["content_marketing", "social_media", "community"]
        elif user_count < 10000:
            return ["paid_ads", "referral_program", "partnerships"]
        else:
            return ["paid_ads", "referral_program", "enterprise_sales", "international_expansion"]

    def _create_experiments(self, channels: list[str], metrics: dict) -> list[GrowthExperiment]:
        experiments = []
        
        channel_experiments = {
            "content_marketing": [("SEO Optimization", "Improve organic traffic by 50%"), ("Blog Content", "Increase blog subscribers by 30%")],
            "social_media": [("Social Campaign", "Grow social followers by 25%"), ("Viral Content", "Create shareable content piece")],
            "paid_ads": [("Facebook Ads", "Achieve $50 CAC"), ("Google Ads", "Reach 10k impressions")],
            "referral_program": [("Referral Incentive", "10% of users invite 1 friend")],
            "partnerships": [("Strategic Partner", "Partner with 3 complementary products")],
        }
        
        for channel in channels:
            for name, hypothesis in channel_experiments.get(channel, []):
                exp = GrowthExperiment(name=name, hypothesis=hypothesis, channel=channel, metric="conversion_rate", target_value=0.1)
                experiments.append(exp)
        
        return experiments

    def _design_funnel(self, metrics: dict) -> dict:
        return {
            "acquisition": {"metric": "visitors", "target": 10000, "current": metrics.get("visitors", 0)},
            "activation": {"metric": "signups", "target": 1000, "current": metrics.get("signups", 0)},
            "retention": {"metric": "active_users", "target": 500, "current": metrics.get("users", 0)},
            "revenue": {"metric": "paying_customers", "target": 100, "current": metrics.get("customers", 0)},
            "referral": {"metric": "referrals", "target": 50, "current": metrics.get("referrals", 0)},
        }

    def _define_growth_metrics(self, metrics: dict) -> dict:
        return {
            "primary": {"metric": "Monthly Active Users", "current": metrics.get("users", 0), "target": metrics.get("users", 0) * 2},
            "secondary": ["Activation rate", "Retention rate", "Revenue per user"],
            "north_star": "Weekly active users who invite another user",
        }

    def _define_strategies(self, metrics: dict) -> list[str]:
        strategies = ["Build product-led growth loops", "Optimize onboarding for activation"]
        if metrics.get("users", 0) > 1000:
            strategies.append("Implement referral program")
        if metrics.get("revenue", 0) > 10000:
            strategies.append("Add enterprise tier")
        return strategies

    def track_experiment(self, experiment_id: str, results: dict) -> dict:
        exp = self.experiments.get(experiment_id)
        if not exp:
            return {"error": "Experiment not found"}
        exp.results = results
        exp.status = "completed"
        return {"status": "updated", "experiment": exp.to_dict()}

    def get_growth_insights(self) -> dict:
        all_strategies = list(self.strategies.values())
        if not all_strategies:
            return {"status": "no_strategies"}
        
        all_experiments = list(self.experiments.values())
        completed = [e for e in all_experiments if e.status == "completed"]
        
        return {
            "total_strategies": len(all_strategies),
            "total_experiments": len(all_experiments),
            "completed_experiments": len(completed),
        }