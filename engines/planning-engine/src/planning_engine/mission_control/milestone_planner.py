"""Milestone Planner — Generate milestones from objective trees"""
import uuid
from datetime import datetime, timezone
from planning_engine.mission_control.objective_tree import ObjectiveTree, ObjectiveType


class MilestonePlanner:
    """Generates time-based milestones from an objective tree."""

    HORIZON_MONTHS = {
        "1m": 1, "3m": 3, "6m": 6, "12m": 12, "1y": 12,
        "2y": 24, "5y": 60,
    }

    def __init__(self, horizon: str = "3m"):
        self.horizon = horizon
        self.total_months = self.HORIZON_MONTHS.get(horizon, 3)

    def generate_milestones(self, tree: ObjectiveTree) -> list[dict]:
        milestones = []
        objectives = list(tree.root.children) if tree.root else []

        for i, obj in enumerate(objectives):
            month_num = self._assign_month(i, len(objectives))
            month_label = f"Month {month_num}"

            milestones.append({
                "id": f"TASK-{uuid.uuid4().hex[:8]}",
                "title": f"[{month_label}] {obj.title}",
                "description": obj.description,
                "objective_id": obj.id,
                "month": month_num,
                "priority": self._calculate_priority(obj, i, len(objectives)),
                "risk": obj.risk_level,
                "success_criteria": obj.success_criteria,
                "status": "pending",
            })

            # Add sub-tasks for key results
            for child in obj.children:
                if child.objective_type == ObjectiveType.KEY_RESULT:
                    milestones.append({
                        "id": f"TASK-{uuid.uuid4().hex[:8]}",
                        "title": f"[{month_label}] {child.title}",
                        "description": f"Key result for: {obj.title}",
                        "objective_id": child.id,
                        "month": month_num,
                        "priority": "medium",
                        "risk": "low",
                        "success_criteria": [],
                        "status": "pending",
                    })

        return milestones

    def _assign_month(self, index: int, total: int) -> int:
        if total == 0:
            return 1
        month = int((index / total) * self.total_months) + 1
        return min(month, self.total_months)

    def _calculate_priority(self, obj, index: int, total: int) -> str:
        if index == 0:
            return "critical"
        elif index < total * 0.3:
            return "high"
        elif index < total * 0.7:
            return "medium"
        else:
            return "low"

    def get_quarter(self, month: int) -> str:
        q = (month - 1) // 3 + 1
        return f"Q{q}"

    def get_month_name(self, month: int) -> str:
        names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return names[(month - 1) % 12]
