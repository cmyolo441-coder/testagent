"""Finance Modeler — Create financial projections"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


@dataclass
class FinancialProjection:
    id: str = field(default_factory=lambda: f"FIN-{uuid.uuid4().hex[:8]}")
    revenue: dict = field(default_factory=dict)
    costs: dict = field(default_factory=dict)
    cash_flow: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {"id": self.id, "revenue": self.revenue, "costs": self.costs, "metrics": self.metrics}


class FinanceModeler:
    """Create and manage financial projections."""

    def __init__(self):
        self.projections: dict[str, FinancialProjection] = {}
        self.cost_categories: list[str] = ["salaries", "infrastructure", "marketing", "operations", "legal", "miscellaneous"]

    def model(self, costs: dict, revenue: dict) -> FinancialProjection:
        """Create financial projection based on costs and revenue estimates."""
        projection = FinancialProjection()
        
        projection.revenue = self._project_revenue(revenue)
        projection.costs = self._project_costs(costs)
        projection.cash_flow = self._calculate_cash_flow(projection.revenue, projection.costs)
        projection.metrics = self._calculate_metrics(projection)
        projection.assumptions = self._list_assumptions()
        
        self.projections[projection.id] = projection
        return projection

    def _project_revenue(self, revenue: dict) -> dict:
        base = revenue.get("base", 0)
        growth_rate = revenue.get("growth_rate", 0.15)
        
        yearly_revenue = {}
        current = base
        for year in range(1, 4):
            current = current * (1 + growth_rate) if current > 0 else base * (1 + growth_rate) ** year
            yearly_revenue[f"year_{year}"] = round(current, 2)
        
        monthly_revenue = yearly_revenue.get("year_1", 0) / 12
        return {
            "monthly": round(monthly_revenue, 2),
            "yearly": yearly_revenue,
            "total_3_year": sum(yearly_revenue.values()),
            "growth_rate": growth_rate,
        }

    def _project_costs(self, costs: dict) -> dict:
        breakdown = {}
        total = 0
        for category in self.cost_categories:
            amount = costs.get(category, 0)
            breakdown[category] = amount
            total += amount
        
        monthly = total / 12
        return {"breakdown": breakdown, "monthly": round(monthly, 2), "yearly": round(total, 2)}

    def _calculate_cash_flow(self, revenue: dict, costs: dict) -> dict:
        monthly_revenue = revenue.get("monthly", 0)
        monthly_costs = costs.get("monthly", 0)
        monthly_burn = monthly_costs - monthly_revenue
        
        runway_months = monthly_revenue / monthly_burn if monthly_burn > 0 else float('inf')
        
        return {
            "monthly_burn": round(monthly_burn, 2),
            "runway_months": round(runway_months, 1),
            "break_even_month": self._calculate_break_even(monthly_revenue, monthly_costs),
        }

    def _calculate_break_even(self, monthly_revenue: float, monthly_costs: float) -> int:
        if monthly_revenue >= monthly_costs:
            return 0
        return int(monthly_costs / max(monthly_revenue, 1)) + 1

    def _calculate_metrics(self, projection: FinancialProjection) -> dict:
        return {
            "gross_margin": 0.7,
            "net_margin": 0.15,
            "ltv_cac_ratio": 3.0,
            "mrr": projection.revenue.get("monthly", 0),
            "arr": projection.revenue.get("yearly", {}).get("year_1", 0),
        }

    def _list_assumptions(self) -> list[str]:
        return ["Revenue grows at projected rate", "No major market disruptions", "Team size scales with revenue", "Infrastructure costs scale linearly"]

    def scenario_analysis(self, projection_id: str) -> dict:
        projection = self.projections.get(projection_id)
        if not projection:
            return {"error": "Projection not found"}
        
        base_revenue = projection.revenue.get("yearly", {}).get("year_1", 0)
        base_costs = projection.costs.get("yearly", 0)
        
        return {
            "optimistic": {"revenue": base_revenue * 1.5, "costs": base_costs * 0.9, "profit": base_revenue * 1.5 - base_costs * 0.9},
            "base": {"revenue": base_revenue, "costs": base_costs, "profit": base_revenue - base_costs},
            "pessimistic": {"revenue": base_revenue * 0.7, "costs": base_costs * 1.1, "profit": base_revenue * 0.7 - base_costs * 1.1},
        }

    def get_finance_insights(self) -> dict:
        all_projections = list(self.projections.values())
        if not all_projections:
            return {"status": "no_projections"}
        return {
            "total_projections": len(all_projections),
            "average_monthly_burn": sum(p.cash_flow.get("monthly_burn", 0) for p in all_projections) / len(all_projections),
        }