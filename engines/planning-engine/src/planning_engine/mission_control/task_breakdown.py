"""Task Breakdown — Decompose objectives into actionable tasks"""
import uuid


class TaskBreakdown:
    """Break down objectives into smaller tasks."""

    def break_down(self, objective_title: str, objective_description: str,
                   max_tasks: int = 10) -> list[dict]:
        tasks = []
        words = objective_title.lower().split()

        # Generic breakdown based on objective type
        phases = ["Research", "Plan", "Implement", "Test", "Review"]
        for i, phase in enumerate(phases[:max_tasks]):
            tasks.append({
                "id": f"TASK-{uuid.uuid4().hex[:8]}",
                "title": f"{phase}: {objective_title[:50]}",
                "description": f"{phase} phase for: {objective_description}",
                "priority": "high" if i < 2 else "medium",
                "risk": "medium" if phase == "Implement" else "low",
            })
        return tasks
