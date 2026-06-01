"""Progress Tracker — Calculate and report mission progress"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ProgressReport:
    mission_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    pending_tasks: int
    progress_percent: float
    on_track: bool
    risk_summary: dict
    last_updated: str
    bottlenecks: list[str]
    estimated_completion: Optional[str] = None


class ProgressTracker:
    """Tracks and reports mission progress with bottleneck detection."""

    def __init__(self):
        self.reports: dict[str, ProgressReport] = {}

    def calculate_progress(self, tasks: list[dict], mission_id: str) -> ProgressReport:
        total = len(tasks)
        completed = sum(1 for t in tasks if t.get("status") == "done")
        failed = sum(1 for t in tasks if t.get("status") == "failed")
        pending = sum(1 for t in tasks if t.get("status") == "pending")
        running = sum(1 for t in tasks if t.get("status") == "running")

        progress = (completed / total * 100) if total > 0 else 0

        risk_summary = self._aggregate_risks(tasks)
        bottlenecks = self._detect_bottlenecks(tasks)
        on_track = self._assess_track(progress, failed, total)

        report = ProgressReport(
            mission_id=mission_id,
            total_tasks=total,
            completed_tasks=completed,
            failed_tasks=failed,
            pending_tasks=pending,
            progress_percent=progress,
            on_track=on_track,
            risk_summary=risk_summary,
            last_updated=datetime.now(timezone.utc).isoformat(),
            bottlenecks=bottlenecks,
        )

        self.reports[mission_id] = report
        return report

    def _aggregate_risks(self, tasks: list[dict]) -> dict:
        risks = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for t in tasks:
            risk = t.get("risk_level", "low")
            if risk in risks:
                risks[risk] += 1
        return risks

    def _detect_bottlenecks(self, tasks: list[dict]) -> list[str]:
        bottlenecks = []
        failed = [t for t in tasks if t.get("status") == "failed"]
        for t in failed:
            bottlenecks.append(f"FAILED: {t.get('title', t.get('id', '?'))}")

        high_risk_pending = [
            t for t in tasks
            if t.get("status") == "pending" and t.get("risk_level") in ("high", "critical")
        ]
        for t in high_risk_pending:
            bottlenecks.append(f"HIGH-RISK PENDING: {t.get('title', t.get('id', '?'))}")

        return bottlenecks

    def _assess_track(self, progress: float, failed: int, total: int) -> bool:
        if total == 0:
            return True
        failure_rate = failed / total
        if failure_rate > 0.2:
            return False
        if progress < 10 and failure_rate > 0:
            return False
        return True

    def get_summary(self, mission_id: str) -> Optional[dict]:
        report = self.reports.get(mission_id)
        if not report:
            return None
        return {
            "mission_id": report.mission_id,
            "progress": f"{report.progress_percent:.1f}%",
            "tasks": f"{report.completed_tasks}/{report.total_tasks}",
            "failed": report.failed_tasks,
            "on_track": report.on_track,
            "bottlenecks": report.bottlenecks,
            "risks": report.risk_summary,
        }
