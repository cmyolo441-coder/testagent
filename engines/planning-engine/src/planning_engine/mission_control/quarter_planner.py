"""Quarter Planner — Quarterly milestone planning"""


class QuarterPlanner:
    """Plan milestones by quarter."""

    def __init__(self, total_months: int = 6):
        self.total_months = total_months

    def get_quarters(self) -> list[dict]:
        quarters = []
        months_per_quarter = 3
        for q in range(1, (self.total_months // months_per_quarter) + 1):
            start_month = (q - 1) * months_per_quarter + 1
            end_month = min(q * months_per_quarter, self.total_months)
            quarters.append({
                "quarter": f"Q{q}",
                "start_month": start_month,
                "end_month": end_month,
                "months": end_month - start_month + 1,
            })
        return quarters
