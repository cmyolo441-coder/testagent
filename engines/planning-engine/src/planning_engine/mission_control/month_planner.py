"""Month Planner — Monthly milestone planning"""


class MonthPlanner:
    """Plan milestones by month."""

    def __init__(self, total_months: int = 6):
        self.total_months = total_months

    def get_months(self) -> list[dict]:
        months = []
        for m in range(1, self.total_months + 1):
            months.append({
                "month": m,
                "label": f"Month {m}",
                "is_first": m == 1,
                "is_last": m == self.total_months,
            })
        return months
