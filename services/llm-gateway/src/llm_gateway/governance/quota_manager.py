"""Quota Manager — Track and enforce usage quotas"""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional


@dataclass
class Quota:
    name: str
    limit: int  # max units
    used: int = 0
    period: str = "daily"  # daily, weekly, monthly
    reset_at: Optional[str] = None
    resource: str = "tokens"  # tokens, requests, cost_cents

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.used)

    @property
    def utilization(self) -> float:
        return self.used / self.limit if self.limit > 0 else 0

    def is_exceeded(self) -> bool:
        return self.used >= self.limit

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "limit": self.limit,
            "used": self.used,
            "remaining": self.remaining,
            "utilization": f"{self.utilization:.1%}",
            "period": self.period,
            "resource": self.resource,
        }


class QuotaManager:
    """Manage usage quotas for API calls, tokens, and costs."""

    def __init__(self):
        self.quotas: dict[str, Quota] = {}
        self.usage_log: list[dict] = []

    def add_quota(self, quota: Quota):
        self.quotas[quota.name] = quota

    def check_quota(self, quota_name: str, amount: int = 1) -> tuple[bool, str]:
        quota = self.quotas.get(quota_name)
        if not quota:
            return True, "No quota defined"

        if quota.is_exceeded():
            return False, f"Quota exceeded: {quota.used}/{quota.limit}"

        if quota.used + amount > quota.limit:
            return False, f"Would exceed quota: {quota.used} + {amount} > {quota.limit}"

        return True, "OK"

    def consume(self, quota_name: str, amount: int = 1) -> bool:
        allowed, reason = self.check_quota(quota_name, amount)
        if not allowed:
            return False

        quota = self.quotas[quota_name]
        quota.used += amount
        self.usage_log.append({
            "quota": quota_name,
            "amount": amount,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "remaining": quota.remaining,
        })
        return True

    def reset_quota(self, quota_name: str):
        quota = self.quotas.get(quota_name)
        if quota:
            quota.used = 0
            quota.reset_at = datetime.now(timezone.utc).isoformat()

    def get_all_quotas(self) -> list[dict]:
        return [q.to_dict() for q in self.quotas.values()]

    def get_usage_summary(self) -> dict:
        return {
            "quotas": self.get_all_quotas(),
            "total_log_entries": len(self.usage_log),
        }
