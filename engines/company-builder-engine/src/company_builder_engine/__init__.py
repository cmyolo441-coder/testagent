"""Company Builder Engine — 6-month software company builder"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid


class CompanyPhase(Enum):
    RESEARCH = "research"
    DESIGN = "design"
    BUILD = "build"
    SECURITY = "security"
    LAUNCH = "launch"
    GROWTH = "growth"


@dataclass
class CompanyPlan:
    id: str = field(default_factory=lambda: f"PLAN-{uuid.uuid4().hex[:8]}")
    mission_id: str = ""
    company_name: str = ""
    domain: str = ""
    current_phase: CompanyPhase = CompanyPhase.RESEARCH
    months_elapsed: int = 0
    milestones: list[dict] = field(default_factory=list)
    teams: list[dict] = field(default_factory=list)
    budget: float = 0
    revenue: float = 0
    users: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "mission_id": self.mission_id,
            "company_name": self.company_name,
            "domain": self.domain,
            "phase": self.current_phase.value,
            "months_elapsed": self.months_elapsed,
            "budget": self.budget,
            "revenue": self.revenue,
            "users": self.users,
        }


class CompanyBuilderEngine:
    """Orchestrate 6-month company building workflow."""

    MONTH_MILESTONES = {
        1: "Market validation & problem research",
        2: "Product spec, architecture & brand",
        3: "MVP build & core features",
        4: "Security audit & deployment",
        5: "Launch & user acquisition",
        6: "Growth & operations",
    }

    def __init__(self):
        self.plans: dict[str, CompanyPlan] = {}

    def create_plan(self, mission_id: str, company_name: str, domain: str = "") -> CompanyPlan:
        plan = CompanyPlan(mission_id=mission_id, company_name=company_name, domain=domain)
        for month, milestone in self.MONTH_MILESTONES.items():
            plan.milestones.append({"month": month, "title": milestone, "status": "pending"})
        self.plans[plan.id] = plan
        return plan

    def advance_month(self, plan_id: str) -> bool:
        plan = self.plans.get(plan_id)
        if not plan or plan.months_elapsed >= 6:
            return False
        plan.months_elapsed += 1
        phase_map = {1: CompanyPhase.RESEARCH, 2: CompanyPhase.DESIGN, 3: CompanyPhase.BUILD,
                     4: CompanyPhase.SECURITY, 5: CompanyPhase.LAUNCH, 6: CompanyPhase.GROWTH}
        plan.current_phase = phase_map.get(plan.months_elapsed, CompanyPhase.GROWTH)
        return True

    def get_progress(self, plan_id: str) -> dict:
        plan = self.plans.get(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        return {
            "plan": plan.to_dict(),
            "milestone": self.MONTH_MILESTONES.get(plan.months_elapsed + 1, "Completed"),
            "progress": plan.months_elapsed / 6 * 100,
        }
