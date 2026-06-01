"""Day Planner — Daily task scheduling"""


class DayPlanner:
    """Plan daily tasks."""

    def __init__(self, working_hours: int = 8):
        self.working_hours = working_hours

    def get_time_blocks(self) -> list[dict]:
        blocks = []
        for hour in range(self.working_hours):
            blocks.append({
                "start": f"{9 + hour:02d}:00",
                "end": f"{10 + hour:02d}:00",
                "hour": hour,
            })
        return blocks
