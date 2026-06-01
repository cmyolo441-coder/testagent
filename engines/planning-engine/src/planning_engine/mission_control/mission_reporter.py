"""Mission Reporter — Generate mission status reports"""


class MissionReporter:
    """Generate comprehensive mission status reports."""

    def generate_report(self, mission: dict, tasks: list[dict], progress: float,
                       risks: dict, checkpoints: list[dict]) -> dict:
        total = len(tasks)
        done = sum(1 for t in tasks if t.get("status") == "done")
        failed = sum(1 for t in tasks if t.get("status") == "failed")
        running = sum(1 for t in tasks if t.get("status") == "running")

        return {
            "mission_id": mission.get("id", "?"),
            "goal": mission.get("goal", "?"),
            "status": mission.get("status", "?"),
            "progress": f"{progress:.1f}%",
            "tasks": {
                "total": total,
                "completed": done,
                "failed": failed,
                "running": running,
                "pending": total - done - failed - running,
            },
            "risks": risks,
            "checkpoints": len(checkpoints),
            "last_checkpoint": checkpoints[-1] if checkpoints else None,
        }
