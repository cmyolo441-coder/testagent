"""Budget Manager — Track costs and budget limits"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BudgetItem:
    description: str
    amount: float
    category: str = "general"
    metadata: dict = field(default_factory=dict)


class BudgetManager:
    """Track mission budgets and costs."""

    def __init__(self, total_budget: float = 0):
        self.total_budget = total_budget
        self.items: list[BudgetItem] = []

    def add_expense(self, description: str, amount: float, category: str = "general"):
        self.items.append(BudgetItem(description=description, amount=amount, category=category))

    @property
    def total_spent(self) -> float:
        return sum(item.amount for item in self.items)

    @property
    def remaining(self) -> float:
        return max(0, self.total_budget - self.total_spent)

    @property
    def utilization(self) -> float:
        return self.total_spent / self.total_budget if self.total_budget > 0 else 0

    def get_by_category(self) -> dict:
        categories = {}
        for item in self.items:
            categories[item.category] = categories.get(item.category, 0) + item.amount
        return categories

    def is_over_budget(self) -> bool:
        return self.total_spent > self.total_budget

    def get_summary(self) -> dict:
        return {
            "total_budget": self.total_budget,
            "total_spent": self.total_spent,
            "remaining": self.remaining,
            "utilization": f"{self.utilization:.1%}",
            "over_budget": self.is_over_budget(),
            "categories": self.get_by_category(),
        }
