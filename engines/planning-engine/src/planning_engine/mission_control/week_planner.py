"""Week Planner — Weekly task scheduling"""


class WeekPlanner:
    """Plan tasks by week within months."""

    def __init__(self, weeks_per_month: int = 4):
        self.weeks_per_month = weeks_per_month

    def get_weeks(self, month: int) -> list[dict]:
        weeks = []
        for w in range(1, self.weeks_per_month + 1):
            weeks.append({
                "month": month,
                "week": w,
                "label": f"M{month}W{w}",
            })
        return weeks
